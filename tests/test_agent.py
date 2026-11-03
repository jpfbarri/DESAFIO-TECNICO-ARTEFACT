import unittest
from uuid import uuid4

from src.agent.llm_client import RateLimitExceededError, execute_with_exponential_backoff
from src.agent.orchestrator import EmporioMusicAgent


class TestEmporioMusicAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = EmporioMusicAgent()
        self.thread_id = f"test-thread-{uuid4().hex[:8]}"

    def tearDown(self) -> None:
        self.agent.checkpointer.clear_thread(self.thread_id)

    def test_scenario_1_violoes_up_to_1000(self) -> None:
        resp = self.agent.run_turn(
            "Quais opções de violões disponíveis custando até R$1000?",
            thread_id=self.thread_id,
        )
        tool_names = [t.tool_name for t in resp.tool_calls]
        self.assertIn("search_products", tool_names)
        self.assertIn("Yamaha C40", resp.reply)
        self.assertNotIn("Giannini GF-3D", resp.reply)

    def test_scenario_2_store_address(self) -> None:
        resp = self.agent.run_turn("Qual o endereço da loja?", thread_id=self.thread_id)
        tool_names = [t.tool_name for t in resp.tool_calls]
        self.assertIn("search_policies", tool_names)
        self.assertIn("Rua 14 de Maio, 3200", resp.reply)

    def test_scenario_3_takamine_gd20_price(self) -> None:
        resp = self.agent.run_turn("Quanto custa o Takamine GD20?", thread_id=self.thread_id)
        tool_names = [t.tool_name for t in resp.tool_calls]
        self.assertIn("get_product_price", tool_names)
        self.assertIn("2199.00", resp.reply)
        self.assertIn("2089.05", resp.reply)
        self.assertIn("EXPIRADA", resp.reply)

    def test_scenario_4_regret_return_policy(self) -> None:
        resp = self.agent.run_turn(
            "Me arrependi da minha compra, posso devolver meu pedido?",
            thread_id=self.thread_id,
        )
        tool_names = [t.tool_name for t in resp.tool_calls]
        self.assertIn("search_policies", tool_names)
        self.assertIn("7 (sete) dias corridos", resp.reply)

    def test_multi_turn_order_status_with_sqlite_checkpointer(self) -> None:
        turn1 = self.agent.run_turn("Qual o status do meu pedido #1?", thread_id=self.thread_id)
        self.assertIn("Verificação de segurança necessária", turn1.reply)

        # Turno 2: o cliente fornece apenas o e-mail, e o agente recupera o pedido #1 da memória SQLite
        turn2 = self.agent.run_turn(
            "Meu e-mail é pedro.oliveira@jmail.com",
            thread_id=self.thread_id,
        )
        tool_names = [t.tool_name for t in turn2.tool_calls]
        self.assertIn("get_order_status", tool_names)
        self.assertIn("BRAB1234567BR", turn2.reply)
        self.assertIn("DELIVERED", turn2.reply)

    def test_out_of_scope_accessories_and_general_topics(self) -> None:
        acc_resp = self.agent.run_turn(
            "Vocês vendem encordoamento de guitarra e palhetas?",
            thread_id=self.thread_id,
        )
        self.assertIn("exclusivamente com instrumentos musicais", acc_resp.reply)
        self.assertIn("não comercializamos acessórios", acc_resp.reply)

        gen_resp = self.agent.run_turn(
            "Me passa uma receita de bolo de chocolate?",
            thread_id=self.thread_id,
        )
        self.assertEqual(len(gen_resp.tool_calls), 0)
        self.assertIn("instrumentos musicais", gen_resp.reply)

    def test_exponential_backoff_retries_on_429(self) -> None:
        attempts = {"count": 0}

        def flaky_operation() -> str:
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise RateLimitExceededError("HTTP 429 Rate Limit")
            return "sucesso"

        result = execute_with_exponential_backoff(flaky_operation, max_retries=3, initial_delay=0.01)
        self.assertEqual(result, "sucesso")
        self.assertEqual(attempts["count"], 3)

    def test_sse_streaming_events_sequence(self) -> None:
        events = list(
            self.agent.stream_turn_sse("Quanto custa o Yamaha C40?", thread_id=self.thread_id)
        )
        event_types = [e["event"] for e in events]
        self.assertIn("tool_start", event_types)
        self.assertIn("tool_end", event_types)
        self.assertIn("token", event_types)
        self.assertEqual(event_types[-1], "done")


if __name__ == "__main__":
    unittest.main()
