import unittest
from src.rag.pdf_section_chunker import load_policy_sections
from src.rag.policy_retriever import PolicyRetriever, search_store_policies


class TestPolicyRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sections = load_policy_sections()
        cls.retriever = PolicyRetriever(sections=cls.sections)

    def test_loads_all_ten_manual_sections(self) -> None:
        self.assertEqual(len(self.sections), 10)
        section_ids = [s.section_id for s in self.sections]
        self.assertEqual(section_ids, [str(i) for i in range(1, 11)])

    def test_retrieves_return_and_regret_policy(self) -> None:
        results = self.retriever.search("Me arrependi da minha compra, posso devolver meu pedido?", top_k=2)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].section.section_id, "4")
        self.assertIn("7 (sete) dias corridos", results[0].section.content)

    def test_retrieves_store_address_and_contact(self) -> None:
        results = self.retriever.search("Qual o endereço da loja em Campo Grande?", top_k=2)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].section.section_id, "1")
        self.assertIn("Rua 14 de Maio, 3200", results[0].section.content)

    def test_retrieves_opening_hours(self) -> None:
        results = self.retriever.search("Qual o horário de funcionamento no sábado e domingo?", top_k=2)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].section.section_id, "2")
        self.assertIn("09:00 às 13:00", results[0].section.content)

    def test_retrieves_payment_and_installment_rules(self) -> None:
        results = self.retriever.search("Tem desconto no PIX e em quantas vezes parcela no cartão?", top_k=2)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].section.section_id, "3")
        self.assertIn("5% de desconto", results[0].section.content)

    def test_retrieves_shipping_and_delivery_rules(self) -> None:
        results = self.retriever.search("Qual o valor do frete e prazo de entrega por SEDEX ou motoboy?", top_k=2)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].section.section_id, "5")
        self.assertIn("R$ 500,00", results[0].section.content)

    def test_retrieves_accessory_exclusion_scope(self) -> None:
        formatted = search_store_policies("Vocês vendem encordoamento, palhetas, cabos ou amplificador?", top_k=2)
        self.assertIn("acessórios", formatted.lower())

    def test_empty_query_returns_empty_list(self) -> None:
        self.assertEqual(self.retriever.search("   "), [])


if __name__ == "__main__":
    unittest.main()

