import json
import sys
from typing import Any, Callable, Dict, List, Optional

from src.tools.store_tools import (
    escalate_to_human,
    get_active_promotions,
    get_order_status,
    get_product_price,
    search_policies,
    search_products,
)

MCP_SERVER_NAME = "emporio-da-musica-mcp"
MCP_SERVER_VERSION = "1.0.0"
MCP_PROTOCOL_VERSION = "2024-11-05"

TOOL_FUNCTIONS_REGISTRY: Dict[str, Callable[..., str]] = {
    "search_products": search_products,
    "get_product_price": get_product_price,
    "get_active_promotions": get_active_promotions,
    "get_order_status": get_order_status,
    "escalate_to_human": escalate_to_human,
    "search_policies": search_policies,
}

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "search_products",
        "description": (
            "Busca instrumentos musicais disponíveis no catálogo da Empório da Música por termo, "
            "categoria (Violões, Guitarras, Baixos, Baterias, Teclados, Sopro, Ukuleles) e preço máximo/mínimo."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Termo livre (ex: 'violão nylon', 'Yamaha', 'dreadnought')"},
                "category": {"type": "string", "description": "Categoria do instrumento (ex: 'Violões', 'Guitarras')"},
                "max_price_brl": {"type": "number", "description": "Preço máximo em R$ (ex: 1000.0)"},
                "min_price_brl": {"type": "number", "description": "Preço mínimo em R$"},
                "only_available": {"type": "boolean", "description": "Se True, retorna apenas produtos ativos com estoque > 0", "default": True},
            },
        },
    },
    {
        "name": "get_product_price",
        "description": (
            "Consulta o preço detalhado de um instrumento específico (por nome ou ID), "
            "verificando estoque atual, desconto de 5% no PIX, regras de parcelamento, "
            "promoções ativas ou expiradas e sugestões de alternativas caso indisponível."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_query": {"type": "string", "description": "Nome do modelo ou ID do produto (ex: 'Takamine GD20', 'Yamaha C40', '95')"},
            },
            "required": ["product_query"],
        },
    },
    {
        "name": "get_active_promotions",
        "description": (
            "Lista todas as promoções atualmente ativas na loja com preços originais e com desconto, "
            "ou verifica se uma campanha específica (ex: 'Black Friday', 'Oferta Especial') está ativa ou expirada."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "campaign_query": {"type": "string", "description": "Opcional: nome da campanha ou produto para checar se a promoção expirou"},
            },
        },
    },
    {
        "name": "get_order_status",
        "description": (
            "Consulta o status, código de rastreamento, previsão de entrega e itens de um pedido. "
            "EXIGE verificação de identidade do cliente (e-mail, telefone ou nome completo cadastrado)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "Número do pedido (ex: 1, 4, 8, 10)"},
                "customer_identifier": {"type": "string", "description": "E-mail, telefone ou nome completo do titular do pedido para validação LGPD"},
            },
            "required": ["order_id", "customer_identifier"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Gera protocolo e transfere o atendimento para um especialista humano da loja "
            "em casos de reclamações, avarias no transporte, dúvidas omissas no manual ou pedido do cliente."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "Nome do cliente"},
                "customer_contact": {"type": "string", "description": "E-mail ou telefone/WhatsApp do cliente"},
                "reason": {"type": "string", "description": "Resumo claro do motivo do escalonamento ou reclamação"},
                "order_id": {"type": "integer", "description": "Opcional: ID do pedido relacionado"},
            },
            "required": ["customer_name", "customer_contact", "reason"],
        },
    },
    {
        "name": "search_policies",
        "description": (
            "Consulta o manual oficial de políticas e procedimentos da Empório da Música "
            "(horário de funcionamento, endereço, formas de pagamento, parcelamento, trocas, "
            "direito de arrependimento em 7 dias, defeitos em 30 dias, frete, garantia de 90 dias, escopo de acessórios e LGPD)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Dúvida ou tema da política (ex: 'devolução arrependimento', 'horário sábado', 'frete Campo Grande')"},
            },
            "required": ["query"],
        },
    },
]


def execute_store_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
    func = TOOL_FUNCTIONS_REGISTRY.get(tool_name)
    if not func:
        raise ValueError(f"Tool '{tool_name}' não registrada no servidor MCP.")
    safe_args = arguments or {}
    return func(**safe_args)


def create_fastmcp_instance() -> Any:
    try:
        from fastmcp import FastMCP
    except ImportError:
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError:
            return None

    mcp = FastMCP(MCP_SERVER_NAME)
    for fn in TOOL_FUNCTIONS_REGISTRY.values():
        mcp.tool()(fn)
    return mcp


def handle_jsonrpc_message(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params") or {}

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": MCP_SERVER_NAME, "version": MCP_SERVER_VERSION},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOL_SCHEMAS}}
    if method == "tools/call":
        return _handle_tools_call_rpc(req_id, params)
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def _handle_tools_call_rpc(req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    tool_name = params.get("name", "")
    arguments = params.get("arguments") or {}
    try:
        output = execute_store_tool(tool_name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": output}], "isError": False},
        }
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": f"Erro na tool {tool_name}: {exc}"}], "isError": True},
        }


def run_stdio_server() -> None:
    fastmcp_app = create_fastmcp_instance()
    if fastmcp_app is not None:
        fastmcp_app.run(transport="stdio")
        return

    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            request = json.loads(stripped)
            response = handle_jsonrpc_message(request)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as err:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(err)}}
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()

