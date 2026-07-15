"""
Tests - Base de Datos y Repositorios

Verifica CRUD de productos, historial y builds.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Product, PriceHistory, Build, BuildItem
from database.database import Database
from repositories.product_repository import ProductRepository
from repositories.history_repository import HistoryRepository
from repositories.build_repository import BuildRepository


class TestDatabase(unittest.TestCase):
    """Tests para la capa de base de datos."""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def test_create_product(self):
        session = self.Session()
        repo = ProductRepository(session)

        product = Product(
            name="RTX 5060",
            category="GPU",
            brand="ASUS",
            model="Dual RTX 5060",
            store="MercadoLibre",
            url="https://mercadolibre.com.co/test",
            current_price=1700000,
            lowest_price=1700000,
            highest_price=1700000,
            currency="COP",
            active=True,
        )
        created = repo.add(product)

        self.assertIsNotNone(created.id)
        self.assertEqual(created.name, "RTX 5060")
        self.assertEqual(created.category, "GPU")
        self.assertEqual(created.current_price, 1700000)

        session.close()

    def test_get_all_products(self):
        session = self.Session()
        repo = ProductRepository(session)

        for i in range(5):
            p = Product(
                name=f"Product {i}",
                category="CPU",
                store="Test",
                url=f"https://test.com/{i}",
                active=True,
            )
            repo.add(p)

        products = repo.get_all()
        self.assertEqual(len(products), 5)

        session.close()

    def test_update_price(self):
        session = self.Session()
        repo = ProductRepository(session)

        p = Product(
            name="Test Product",
            category="RAM",
            store="Test",
            url="https://test.com",
            current_price=100000,
            active=True,
        )
        repo.add(p)

        updated = repo.update_price(p.id, 90000)

        self.assertIsNotNone(updated)
        self.assertEqual(updated.current_price, 90000)
        self.assertEqual(updated.previous_price, 100000)
        self.assertEqual(updated.lowest_price, 90000)

        session.close()

    def test_delete_product(self):
        session = self.Session()
        repo = ProductRepository(session)

        p = Product(
            name="To Delete",
            category="SSD",
            store="Test",
            url="https://test.com",
            active=True,
        )
        repo.add(p)
        product_id = p.id

        result = repo.delete(product_id)
        self.assertTrue(result)

        fetched = repo.get_by_id(product_id)
        self.assertIsNotNone(fetched)
        self.assertFalse(fetched.active)

        session.close()

    def test_search_products(self):
        session = self.Session()
        repo = ProductRepository(session)

        repo.add(Product(name="ASUS RTX 5060", category="GPU", store="ML", url="https://a.com", active=True))
        repo.add(Product(name="Ryzen 7500F", category="CPU", store="ML", url="https://b.com", active=True))
        repo.add(Product(name="ASUS Motherboard", category="Motherboard", store="ML", url="https://c.com", active=True))

        results = repo.search("ASUS")
        self.assertEqual(len(results), 2)

        results = repo.search("Ryzen")
        self.assertEqual(len(results), 1)

        session.close()


class TestHistory(unittest.TestCase):
    """Tests para el repositorio de historial."""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def test_add_history_record(self):
        session = self.Session()
        history_repo = HistoryRepository(session)

        record = history_repo.add_record(product_id=1, price=500000)
        self.assertIsNotNone(record.id)
        self.assertEqual(record.price, 500000)

        session.close()

    def test_get_min_max_price(self):
        session = self.Session()
        history_repo = HistoryRepository(session)

        history_repo.add_record(product_id=1, price=500000)
        history_repo.add_record(product_id=1, price=450000)
        history_repo.add_record(product_id=1, price=550000)

        min_price = history_repo.get_min_price(1)
        max_price = history_repo.get_max_price(1)

        self.assertEqual(min_price, 450000)
        self.assertEqual(max_price, 550000)

        session.close()


class TestBuilds(unittest.TestCase):
    """Tests para el repositorio de builds."""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def _create_test_products(self, session):
        products = []
        data = [
            ("RTX 5060", "GPU", 1700000),
            ("Ryzen 7500F", "CPU", 487000),
            ("DDR5 32GB", "RAM", 300000),
        ]
        for name, cat, price in data:
            p = Product(
                name=name, category=cat, store="ML",
                url=f"https://test.com/{name}",
                current_price=price, lowest_price=price,
                active=True,
            )
            session.add(p)
            session.flush()
            products.append(p)
        session.commit()
        return products

    def test_create_build(self):
        session = self.Session()
        build_repo = BuildRepository(session)
        products = self._create_test_products(session)

        build = build_repo.create_build(
            "PC Gamer", [p.id for p in products]
        )
        self.assertIsNotNone(build.id)
        self.assertEqual(build.name, "PC Gamer")

        session.close()

    def test_build_total(self):
        session = self.Session()
        build_repo = BuildRepository(session)
        products = self._create_test_products(session)

        build = build_repo.create_build(
            "PC Test", [p.id for p in products]
        )

        totals = build_repo.get_build_total(build.id)
        self.assertEqual(totals["total_current"], 1700000 + 487000 + 300000)
        self.assertEqual(len(totals["items"]), 3)

        session.close()

    def test_delete_build(self):
        session = self.Session()
        build_repo = BuildRepository(session)

        build = build_repo.create_build("To Delete", [])

        result = build_repo.delete_build(build.id)
        self.assertTrue(result)

        fetched = build_repo.get_by_id(build.id)
        self.assertIsNone(fetched)

        session.close()


if __name__ == "__main__":
    unittest.main()
