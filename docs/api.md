# Contrato da API — Empório da Música (FastAPI + SSE)

A API do backend expõe endpoints REST e Server-Sent Events (SSE) para comunicação em tempo real com o agente ReAct da **Empório da Música**.

---

## 1. Endpoints Disponíveis

| Método | Rota | Descrição |
| :---: | :--- | :--- |
| `GET` | `/health` | Status da aplicação, modelo LLM configurado, contagem de produtos no SQLite e tools MCP ativas. |
| `POST` | `/api/chat` | Resposta síncrona completa do agente (`AgentTurnResponse`). |
| `POST` | `/api/chat/stream` | Streaming em tempo real via Server-Sent Events (`text/event-stream`). |
| `GET` | `/api/threads/{thread_id}/history` | Recupera o histórico persistido no SQLite para a conversa `thread_id`. |
| `DELETE` | `/api/threads/{thread_id}` | Limpa a memória de conversa do `thread_id` informado. |
| `GET` | `/api/catalog/highlights` | Lista promoções ativas e categorias para sugestões visuais na UI. |

---

## 2. Contrato de Streaming SSE (`POST /api/chat/stream`)

### Payload de Entrada (`application/json`)
```json
{
  "message": "Quais opções de violões disponíveis custando até R$1000?",
  "thread_id": "session-a1b2c3d4"
}
```

### Eventos Emitidos (`text/event-stream`)

1. **`tool_start`** — Disparado imediatamente antes de o agente invocar uma tool do servidor MCP/RAG:
```text
event: tool_start
data: {"tool": "search_products", "args": {"category": "Violões", "max_price_brl": 1000.0, "only_available": true}}
```

2. **`tool_end`** — Disparado assim que a tool retorna os dados consultados:
```text
event: tool_end
data: {"tool": "search_products", "output_preview": "Encontrados 9 instrumento(s):\n- [ID 83] Tagima Memphis AC-39 Nylon Natural..."}
```

3. **`token`** — Disparado incrementalmente durante a geração da resposta final:
```text
event: token
data: {"text": "Olá! Aqui está o que "}
```

4. **`done`** — Disparado ao concluir o turno e persistir no checkpointer SQLite:
```text
event: done
data: {"thread_id": "session-a1b2c3d4", "tools_used": ["search_products"]}
```

5. **`error`** — Disparado em caso de falha inesperada durante o processamento:
```text
event: error
data: {"message": "Descrição técnica do erro"}
```

