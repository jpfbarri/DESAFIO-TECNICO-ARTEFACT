import unittest
from src.tools.mcp_server import handle_jsonrpc_message
from src.tools.store_tools import (
    escalate_to_human,
    get_active_promotions,
    get_order_status,
    get_product_price,
    search_policies,
    search_products,
)


class TestStoreToolsAndMCP(unittest.TestCase):
    def test_search_violoes_up_to_1000_excludes_out_of_stock_and_discontinued(self) -> None:
        output = search_products(category="Violões", max_price_brl=1000.0, only_available=True)
        self.assertIn("Yamaha C40", output)
        self.assertIn("Yamaha C70", output)
        # Garante que violão sem estoque (Giannini GF-3D) e descontinuado (Shelby SN-7C) não aparecem como disponíveis
        self.assertNotIn("Giannini GF-3D", output)
        self.assertNotIn("Shelby SN-7C", output)

    def test_get_product_price_takamine_gd20_flags_expired_promotion(self) -> None:
        output = get_product_price("Takamine GD20")
        self.assertIn("Takamine GD20 Dreadnought Natural", output)
        self.assertIn("R$ 2199.00", output)
        self.assertIn("R$ 2089.05", output)
        self.assertIn("EXPIRADA/INATIVA", output)

    def test_get_product_price_active_promo_warns_non_cumulative_pix(self) -> None:
        output = get_product_price("Taylor 110e")
        self.assertIn("Promoção Ativa", output)
        self.assertIn("8% OFF", output)
        self.assertIn("NÃO se aplica sobre preços já promocionais", output)

    def test_get_product_price_out_of_stock_suggests_alternatives(self) -> None:
        output = get_product_price("Giannini GF-3D")
        self.assertIn("Quantidade em Estoque: 0", output)
        self.assertIn("Alternativas disponíveis na mesma categoria:", output)

    def test_get_active_promotions_lists_active_and_detects_expired_campaign(self) -> None:
        output = get_active_promotions(campaign_query="Black Friday")
        self.assertIn("Promoções expiradas/encerradas encontradas para 'Black Friday'", output)
        self.assertIn("Promoções ATIVAS no sistema (4 encontradas):", output)
        self.assertIn("Ohana CK-20 Concert Natural", output)

    def test_get_order_status_blocks_unverified_identity_lgpd(self) -> None:
        denied = get_order_status(order_id=1, customer_identifier="outro.email@teste.com")
        self.assertIn("Verificação de identidade recusada", denied)
        self.assertNotIn("BRAB1234567BR", denied)

    def test_get_order_status_succeeds_with_valid_email_or_name(self) -> None:
        verified = get_order_status(order_id=1, customer_identifier="pedro.oliveira@jmail.com")
        self.assertIn("Status Atual: DELIVERED", verified)
        self.assertIn("BRAB1234567BR", verified)
        self.assertIn("Martin D-28", verified)

        shipped = get_order_status(order_id=8, customer_identifier="Ana Carolina Ferreira")
        self.assertIn("Status Atual: SHIPPED", shipped)
        self.assertIn("BRJL5544332BR", shipped)

    def test_escalate_to_human_generates_protocol_and_sla(self) -> None:
        output = escalate_to_human(
            customer_name="Lucas Mendes",
            customer_contact="lucas.mendes@jmail.com",
            reason="Dúvida sobre troca fora do prazo",
            order_id=4,
        )
        self.assertIn("EMP-", output)
        self.assertIn("24 horas úteis", output)
        self.assertIn("(67) 3321-4500", output)

    def test_mcp_jsonrpc_protocol_initialize_list_and_call(self) -> None:
        init_resp = handle_jsonrpc_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init_resp["result"]["serverInfo"]["name"], "emporio-da-musica-mcp")

        list_resp = handle_jsonrpc_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tool_names = [t["name"] for t in list_resp["result"]["tools"]]
        self.assertEqual(
            set(tool_names),
            {
                "search_products",
                "get_product_price",
                "get_active_promotions",
                "get_order_status",
                "escalate_to_human",
                "search_policies",
            },
        )

        call_resp = handle_jsonrpc_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "search_policies", "arguments": {"query": "horário sábado"}},
            }
        )
        self.assertFalse(call_resp["result"]["isError"])
        self.assertIn("09:00 às 13:00", call_resp["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()

