"""
PC Parts Tracker - Proveedor JSON

Lee precios desde un archivo JSON generado por excel_to_json.py.
Alternativa al scraping cuando las tiendas bloquean.
"""

import json
from pathlib import Path

from providers.base import Provider
from utils.logger import get_logger

logger = get_logger("providers.json_source")

PRICES_FILE = Path(__file__).parent.parent / "data" / "prices.json"


class JsonProvider(Provider):
    """Proveedor que lee precios desde un archivo JSON local."""

    def __init__(self, json_path: Path | None = None) -> None:
        self._path = json_path or PRICES_FILE

    @property
    def name(self) -> str:
        return "JSON"

    def matches_url(self, url: str) -> bool:
        return True

    def get_price(self, url: str, headless: bool = True) -> float | None:
        return None

    def load_prices(self) -> dict[str, float]:
        """
        Carga todos los precios del JSON.

        Returns:
            Dict con URL -> precio.
        """
        if not self._path.exists():
            logger.warning("Archivo JSON no encontrado: %s", self._path)
            return {}

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)

            prices = {}
            for item in data:
                item_url = item.get("url", "")
                item_price = item.get("price")
                if item_url and item_price is not None:
                    prices[item_url] = float(item_price)

            logger.info("Precios JSON cargados: %d productos", len(prices))
            return prices

        except (json.JSONDecodeError, OSError) as e:
            logger.error("Error leyendo JSON: %s", e)
            return {}

    def load_all(self) -> list[dict]:
        """Carga todos los productos del JSON."""
        if not self._path.exists():
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def reload(self) -> None:
        """Recarga el archivo JSON."""
        logger.info("Recargando precios JSON")
