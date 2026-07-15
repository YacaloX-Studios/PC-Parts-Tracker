"""
Tests - Proveedores

Verifica detección de URLs y parseo de precios.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest

try:
    from providers.base import Provider
    from providers.manager import ProviderManager
    from providers.mercadolibre import MercadoLibreProvider
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright no instalado")
class TestMercadoLibreProvider(unittest.TestCase):
    """Tests para el proveedor de MercadoLibre."""

    def setUp(self):
        self.provider = MercadoLibreProvider()

    def test_name(self):
        self.assertEqual(self.provider.name, "MercadoLibre")

    def test_matches_url_mercadolibre(self):
        urls = [
            "https://articulo.mercadolibre.com.co/MCO-123456",
            "https://www.mercadolibre.com.co/producto/p/MCO123",
            "https://mercadolibre.com.co/item",
        ]
        for url in urls:
            self.assertTrue(self.provider.matches_url(url), f"Deberia matchear: {url}")

    def test_matches_url_other(self):
        urls = [
            "https://www.amazon.com/product",
            "https://www.newegg.com/item",
            "https://www.amd.com/buy",
        ]
        for url in urls:
            self.assertFalse(self.provider.matches_url(url), f"No deberia matchear: {url}")

    def test_parse_price_integer(self):
        price = MercadoLibreProvider._parse_price("534374")
        self.assertEqual(price, 534374.0)

    def test_parse_price_with_dots(self):
        price = MercadoLibreProvider._parse_price("534.374")
        self.assertEqual(price, 534374.0)

    def test_parse_price_with_comma(self):
        price = MercadoLibreProvider._parse_price("1,700,000")
        self.assertEqual(price, 1700000.0)

    def test_parse_price_with_currency_symbol(self):
        price = MercadoLibreProvider._parse_price("$534374")
        self.assertEqual(price, 534374.0)

    def test_parse_price_decimal_comma(self):
        price = MercadoLibreProvider._parse_price("534,37")
        self.assertAlmostEqual(price, 534.37, places=2)

    def test_parse_price_invalid(self):
        self.assertIsNone(MercadoLibreProvider._parse_price(""))
        self.assertIsNone(MercadoLibreProvider._parse_price("abc"))
        self.assertIsNone(MercadoLibreProvider._parse_price("$0"))
        self.assertIsNone(MercadoLibreProvider._parse_price("-100"))


@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright no instalado")
class TestProviderManager(unittest.TestCase):
    """Tests para el gestor de proveedores."""

    def setUp(self):
        self.manager = ProviderManager()
        self.manager.register(MercadoLibreProvider())

    def test_detect_mercadolibre(self):
        provider = self.manager.detect_provider(
            "https://articulo.mercadolibre.com.co/MCO-123"
        )
        self.assertIsNotNone(provider)
        self.assertEqual(provider.name, "MercadoLibre")

    def test_detect_unknown(self):
        provider = self.manager.detect_provider(
            "https://www.unknown-store.com/product"
        )
        self.assertIsNone(provider)

    def test_provider_names(self):
        names = self.manager.provider_names
        self.assertIn("MercadoLibre", names)


if __name__ == "__main__":
    unittest.main()
