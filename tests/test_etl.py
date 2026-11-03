import sqlite3
import unittest
from pathlib import Path
from pydantic import ValidationError

from src.database.connection import get_db_connection
from src.etl.clean_and_load import run_etl
from src.models.schemas import Customer, Product


class TestETLPipeline(unittest.TestCase):
    def test_etl_execution_and_row_counts(self):
        counts = run_etl()
        self.assertEqual(counts["categories"], 9)
        self.assertEqual(counts["customers"], 50)
        self.assertEqual(counts["products"], 65)
        self.assertEqual(counts["promotions"], 25)
        self.assertEqual(counts["orders"], 20)
        self.assertEqual(counts["order_items"], 22)

    def test_database_foreign_key_integrity(self):
        with get_db_connection() as conn:
            violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
            self.assertEqual(len(violations), 0, f"Violações de integridade referencial: {violations}")

    def test_product_prices_and_stocks_positive(self):
        with get_db_connection() as conn:
            invalid_prices = conn.execute("SELECT COUNT(*) FROM products WHERE price_brl <= 0;").fetchone()[0]
            self.assertEqual(invalid_prices, 0)
            invalid_stocks = conn.execute("SELECT COUNT(*) FROM products WHERE stock_quantity < 0;").fetchone()[0]
            self.assertEqual(invalid_stocks, 0)

    def test_pydantic_validation_guards(self):
        with self.assertRaises(ValidationError):
            # Preço negativo deve falhar
            Product(
                product_id=999,
                price_brl=-50.0,
                name="Violão Inválido",
                category_id=1,
                description="Teste",
                stock_quantity=10,
                status="active",
                specs="{}",
                created_at="2025-01-01",
            )

        with self.assertRaises(ValidationError):
            # Email sem @ deve falhar
            Customer(
                customer_id=999,
                name="Cliente Teste",
                phone="6799999999",
                email="email_sem_arroba.com",
                city="Campo Grande",
            )


if __name__ == "__main__":
    unittest.main()
