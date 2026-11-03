import json
from typing import Any, Dict, Generator, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agent.llm_client import get_configured_provider_and_model
from src.agent.orchestrator import AgentTurnResponse, EmporioMusicAgent
from src.database.connection import get_db_connection
from src.tools.mcp_server import TOOL_SCHEMAS

API_TITLE = "Empório da Música — AI Customer Support API"
API_VERSION = "1.0.0"

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="API de atendimento inteligente da Empório da Música (Campo Grande/MS) com ReAct, MCP Tools, RAG e Streaming SSE.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_agent_instance: Optional[EmporioMusicAgent] = None


def get_agent() -> EmporioMusicAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = EmporioMusicAgent()
    return _agent_instance


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensagem enviada pelo cliente")
    thread_id: str = Field(default="default-session", description="ID único da sessão/conversa")


@app.get("/health")
def health_check() -> Dict[str, Any]:
    provider, model = get_configured_provider_and_model()
    with get_db_connection() as conn:
        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    return {
        "status": "ok",
        "store": "Empório da Música (Campo Grande/MS)",
        "llm_provider": provider,
        "llm_model": model,
        "products_indexed": product_count,
        "mcp_tools": [t["name"] for t in TOOL_SCHEMAS],
    }


@app.post("/api/chat", response_model=AgentTurnResponse)
def chat_sync(payload: ChatRequest) -> AgentTurnResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="A mensagem não pode estar vazia.")
    agent = get_agent()
    return agent.run_turn(user_message=payload.message, thread_id=payload.thread_id)


def generate_sse_chunks(payload: ChatRequest) -> Generator[str, None, None]:
    agent = get_agent()
    for event_obj in agent.stream_turn_sse(
        user_message=payload.message, thread_id=payload.thread_id
    ):
        ev_name = event_obj["event"]
        ev_data = json.dumps(event_obj["data"], ensure_ascii=False)
        yield f"event: {ev_name}\ndata: {ev_data}\n\n"


@app.post("/api/chat/stream")
def chat_stream(payload: ChatRequest) -> StreamingResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="A mensagem não pode estar vazia.")
    return StreamingResponse(
        generate_sse_chunks(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/threads/{thread_id}/history")
def get_thread_history(thread_id: str) -> Dict[str, Any]:
    agent = get_agent()
    records = agent.checkpointer.get_history(thread_id=thread_id)
    return {
        "thread_id": thread_id,
        "messages": [r.model_dump() for r in records],
    }


@app.delete("/api/threads/{thread_id}")
def clear_thread_history(thread_id: str) -> Dict[str, str]:
    agent = get_agent()
    agent.checkpointer.clear_thread(thread_id=thread_id)
    return {"status": "cleared", "thread_id": thread_id}


@app.get("/api/catalog/highlights")
def get_catalog_highlights() -> Dict[str, List[Dict[str, Any]]]:
    with get_db_connection() as conn:
        promos = conn.execute(
            """
            SELECT p.product_id, p.name, p.price_brl, pr.discount_percent, pr.description AS campaign
            FROM promotions pr
            JOIN products p ON pr.product_id = p.product_id
            WHERE pr.is_active = 1
            ORDER BY pr.discount_percent DESC
            """
        ).fetchall()
        categories = conn.execute(
            "SELECT category_id, name, description FROM categories ORDER BY category_id"
        ).fetchall()
    return {
        "active_promotions": [dict(r) for r in promos],
        "categories": [dict(r) for r in categories],
    }

