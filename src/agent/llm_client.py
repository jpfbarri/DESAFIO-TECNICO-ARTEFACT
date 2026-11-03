import json
import logging
import os
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import requests
from dotenv import load_dotenv

from src.agent.prompts import EMPORIO_SYSTEM_PROMPT
from src.tools.mcp_server import TOOL_SCHEMAS

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_LLM_PROVIDER = "google"
DEFAULT_GOOGLE_MODEL = "gemini-2.0-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-latest"

MAX_RETRIES_ON_429 = 4
INITIAL_BACKOFF_SECONDS = 1.5
BACKOFF_MULTIPLIER = 2.0
JITTER_MAX_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 25


class RateLimitExceededError(Exception):
    """Exceção lançada quando a API retorna HTTP 429 (Rate Limit)."""


def execute_with_exponential_backoff(
    operation: Callable[[], Any],
    max_retries: int = MAX_RETRIES_ON_429,
    initial_delay: float = INITIAL_BACKOFF_SECONDS,
) -> Any:
    """Executa chamada ao LLM com retry e backoff exponencial para erros 429 do free tier."""
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except Exception as err:
            err_msg = str(err).lower()
            is_rate_limit = (
                isinstance(err, RateLimitExceededError)
                or "429" in err_msg
                or "rate limit" in err_msg
                or "quota" in err_msg
                or "resource_exhausted" in err_msg
            )
            if not is_rate_limit or attempt == max_retries:
                raise
            sleep_time = delay + random.uniform(0.0, JITTER_MAX_SECONDS)
            logger.warning(
                "HTTP 429 detectado (tentativa %d/%d). Aguardando %.2fs antes do retry...",
                attempt + 1,
                max_retries,
                sleep_time,
            )
            time.sleep(sleep_time)
            delay *= BACKOFF_MULTIPLIER


def get_configured_provider_and_model() -> Tuple[str, str]:
    provider = os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower()
    model = os.getenv("LLM_MODEL", "").strip()
    if not model:
        if provider == "openai":
            model = DEFAULT_OPENAI_MODEL
        elif provider == "anthropic":
            model = DEFAULT_ANTHROPIC_MODEL
        else:
            model = DEFAULT_GOOGLE_MODEL
    return provider, model


def has_active_api_key() -> bool:
    provider, _ = get_configured_provider_and_model()
    if provider == "google":
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
    elif provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
    else:
        key = None
    return bool(key and key.strip() and not key.strip().startswith("your_"))


def call_gemini_rest_api(
    messages: List[Dict[str, Any]],
    model: str,
    api_key: str,
    enable_tools: bool = True,
) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    contents = _convert_messages_to_gemini_contents(messages)
    payload: Dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": EMPORIO_SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.2},
    }
    if enable_tools:
        payload["tools"] = [{"functionDeclarations": _build_gemini_function_declarations()}]

    def _do_post() -> Dict[str, Any]:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        if resp.status_code == 429:
            raise RateLimitExceededError(f"Gemini 429 Rate Limit: {resp.text}")
        resp.raise_for_status()
        return resp.json()

    return execute_with_exponential_backoff(_do_post)


def _convert_messages_to_gemini_contents(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    contents: List[Dict[str, Any]] = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": str(msg["content"])}]})
    return contents


def _build_gemini_function_declarations() -> List[Dict[str, Any]]:
    declarations = []
    for schema in TOOL_SCHEMAS:
        props = {}
        for prop_name, prop_def in schema["inputSchema"].get("properties", {}).items():
            props[prop_name] = {
                "type": prop_def["type"].upper(),
                "description": prop_def.get("description", ""),
            }
        declarations.append(
            {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": {
                    "type": "OBJECT",
                    "properties": props,
                    "required": schema["inputSchema"].get("required", []),
                },
            }
        )
    return declarations
