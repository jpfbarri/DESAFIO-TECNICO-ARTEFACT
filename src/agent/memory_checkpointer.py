import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.database.connection import get_db_connection

MAX_HISTORY_MESSAGES = 20


class ChatMessageRecord(BaseModel):
    role: str = Field(..., description="Papel da mensagem: user, assistant ou tool")
    content: str = Field(..., description="Conteúdo textual da mensagem")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools acionadas no turno")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp ISO da mensagem",
    )


class SQLiteConversationCheckpointer:
    """Persistência de histórico de conversas por thread_id em SQLite (compatível com LangGraph)."""

    def __init__(self) -> None:
        self._ensure_checkpoint_table()

    def _ensure_checkpoint_table(self) -> None:
        with get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_checkpoints (
                    checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_checkpoints_thread ON conversation_checkpoints(thread_id);"
            )
            conn.commit()

    def save_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatMessageRecord:
        record = ChatMessageRecord(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
        )
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversation_checkpoints (thread_id, role, content, tool_calls_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    record.role,
                    record.content,
                    json.dumps(record.tool_calls, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()
        return record

    def get_history(self, thread_id: str, limit: int = MAX_HISTORY_MESSAGES) -> List[ChatMessageRecord]:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT role, content, tool_calls_json, created_at
                FROM conversation_checkpoints
                WHERE thread_id = ?
                ORDER BY checkpoint_id DESC
                LIMIT ?
                """,
                (thread_id, limit),
            ).fetchall()
        ordered_rows = list(reversed(rows))
        return [
            ChatMessageRecord(
                role=row["role"],
                content=row["content"],
                tool_calls=json.loads(row["tool_calls_json"] or "[]"),
                created_at=row["created_at"],
            )
            for row in ordered_rows
        ]

    def clear_thread(self, thread_id: str) -> None:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM conversation_checkpoints WHERE thread_id = ?", (thread_id,))
            conn.commit()

