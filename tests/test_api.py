import unittest
from uuid import uuid4

from src.api.app import (
    ChatRequest,
    chat_stream,
    chat_sync,
    clear_thread_history,
    generate_sse_chunks,
    get_catalog_highlights,
    get_thread_history,
    health_check,
)


class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.thread_id = f"api-test-{uuid4().hex[:8]}"

    def tearDown(self) -> None:
        clear_thread_history(self.thread_id)

    def test_health_endpoint_returns_store_and_tools(self) -> None:
        res = health_check()
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["products_indexed"], 65)
        self.assertIn("search_products", res["mcp_tools"])
        self.assertIn("search_policies", res["mcp_tools"])

    def test_chat_sync_endpoint_and_history_persistence(self) -> None:
        req = ChatRequest(message="Qual o horário de funcionamento no sábado?", thread_id=self.thread_id)
        resp = chat_sync(req)
        self.assertEqual(resp.thread_id, self.thread_id)
        self.assertIn("09:00 às 13:00", resp.reply)

        hist = get_thread_history(self.thread_id)
        self.assertEqual(len(hist["messages"]), 2)
        self.assertEqual(hist["messages"][0]["role"], "user")
        self.assertEqual(hist["messages"][1]["role"], "assistant")

    def test_chat_stream_sse_protocol_format(self) -> None:
        req = ChatRequest(message="Quanto custa o Takamine GD20?", thread_id=self.thread_id)
        streaming_resp = chat_stream(req)
        self.assertEqual(streaming_resp.media_type, "text/event-stream")

        raw_sse = "".join(list(generate_sse_chunks(req)))
        self.assertIn("event: tool_start", raw_sse)
        self.assertIn("event: tool_end", raw_sse)
        self.assertIn("event: token", raw_sse)
        self.assertIn("event: done", raw_sse)
        self.assertIn("2199.00", raw_sse)

    def test_catalog_highlights_returns_promotions_and_categories(self) -> None:
        highlights = get_catalog_highlights()
        self.assertEqual(len(highlights["active_promotions"]), 4)
        self.assertEqual(len(highlights["categories"]), 9)


if __name__ == "__main__":
    unittest.main()

