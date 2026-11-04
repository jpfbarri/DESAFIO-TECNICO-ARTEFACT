import json
import logging
import os
import random
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import requests
from dotenv import load_dotenv

from src.agent.prompts import EMPORIO_SYSTEM_PROMPT
from src.tools.mcp_server import TOOL_SCHEMAS

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_LLM_PROVIDER = "groq"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GOOGLE_MODEL = "gemini-3.1-flash-lite"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "llama3.2"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-latest"

MAX_RETRIES_ON_ERROR = 3
INITIAL_BACKOFF_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2.0
JITTER_MAX_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 15


class RateLimitExceededError(Exception):
    """Exceção lançada quando a API retorna HTTP 429 ou 503 temporário."""


def execute_with_exponential_backoff(
    operation: Callable[[], Any],
    max_retries: int = MAX_RETRIES_ON_ERROR,
    initial_delay: float = INITIAL_BACKOFF_SECONDS,
) -> Any:
    """Executa chamada ao LLM com retry e backoff exponencial."""
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except Exception as err:
            err_msg = str(err).lower()
            is_transient_error = (
                isinstance(err, RateLimitExceededError)
                or "429" in err_msg
                or "503" in err_msg
                or "rate limit" in err_msg
                or "quota" in err_msg
                or "resource_exhausted" in err_msg
                or "high demand" in err_msg
                or "unavailable" in err_msg
                or "timeout" in err_msg
            )
            if not is_transient_error or attempt == max_retries:
                raise
            retry_after_match = re.search(r"try again in (\d+(?:\.\d+)?)s", str(err))
            if retry_after_match:
                sleep_time = float(retry_after_match.group(1)) + 0.5
            else:
                sleep_time = delay + random.uniform(0.0, JITTER_MAX_SECONDS)
            logger.warning(
                "Instabilidade transiente na API LLM (%s) - tentativa %d/%d. Aguardando %.2fs...",
                type(err).__name__,
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
        if provider == "groq":
            model = DEFAULT_GROQ_MODEL
        elif provider in ("openai", "openrouter"):
            model = DEFAULT_OPENAI_MODEL
        elif provider in ("ollama", "local"):
            model = DEFAULT_OLLAMA_MODEL
        elif provider == "anthropic":
            model = DEFAULT_ANTHROPIC_MODEL
        else:
            model = DEFAULT_GOOGLE_MODEL
    return provider, model


def has_active_api_key() -> bool:
    provider, _ = get_configured_provider_and_model()
    if provider in ("ollama", "local"):
        return True
    if provider == "groq":
        key = os.getenv("GROQ_API_KEY")
    elif provider == "google":
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
    elif provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
    else:
        key = None
    return bool(key and key.strip() and not key.strip().startswith("your_"))


def call_openai_compatible_api(
    messages: List[Dict[str, Any]],
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Suporta Ollama, LM Studio, Groq, OpenRouter ou OpenAI nativo."""
    target_base = base_url or os.getenv("LLM_BASE_URL")
    provider, _ = get_configured_provider_and_model()

    if not target_base:
        if provider == "ollama":
            target_base = "http://localhost:11434/v1"
        elif provider == "local":
            target_base = "http://localhost:1234/v1"
        elif provider == "groq":
            target_base = "https://api.groq.com/openai/v1"
        elif provider == "openrouter":
            target_base = "https://openrouter.ai/api/v1"
        else:
            target_base = "https://api.openai.com/v1"

    url = f"{target_base.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if provider == "groq":
        actual_key = os.getenv("GROQ_API_KEY") or api_key
    elif provider == "openrouter":
        actual_key = os.getenv("OPENROUTER_API_KEY") or api_key
    elif provider in ("ollama", "local"):
        actual_key = "dummy-local-key"
    else:
        actual_key = api_key or os.getenv("OPENAI_API_KEY") or "dummy-key"
    headers["Authorization"] = f"Bearer {actual_key}"

    formatted_messages = [{"role": "system", "content": EMPORIO_SYSTEM_PROMPT}]
    for m in messages:
        formatted_messages.append({"role": m["role"], "content": str(m["content"])})

    payload = {
        "model": model,
        "messages": formatted_messages,
        "temperature": 0.2,
    }

    def _do_post() -> Dict[str, Any]:
        resp = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        if resp.status_code in (429, 503):
            raise RateLimitExceededError(f"HTTP {resp.status_code}: {resp.text}")
        if not resp.ok:
            raise RuntimeError(f"HTTP {resp.status_code} na API LLM ({model}): {resp.text}")
        return resp.json()

    return execute_with_exponential_backoff(_do_post)


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
        if resp.status_code in (429, 503):
            raise RateLimitExceededError(f"Gemini {resp.status_code} Transient: {resp.text}")
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
