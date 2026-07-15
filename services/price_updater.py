"""
PC Parts Tracker - Servicio de Actualización de Precios

Gestiona la actualización individual y masiva de precios,
con soporte para caché, progreso y alertas.
"""

import json
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

import time as _time

from database.models import Product
from repositories.product_repository import ProductRepository
from repositories.history_repository import HistoryRepository
from providers.manager import ProviderManager
from utils.cache import PriceCache
from utils.logger import get_logger

logger = get_logger("services.price_updater")


class UpdateResult:
    """Resultado de una actualización de precio."""

    def __init__(
        self,
        product_id: int,
        product_name: str,
        old_price: float | None,
        new_price: float | None,
        success: bool,
        error: str | None = None,
    ) -> None:
        self.product_id = product_id
        self.product_name = product_name
        self.old_price = old_price
        self.new_price = new_price
        self.success = success
        self.error = error

    @property
    def change_pct(self) -> float | None:
        """Cambio porcentual del precio."""
        if self.old_price and self.new_price and self.old_price > 0:
            return ((self.new_price - self.old_price) / self.old_price) * 100
        return None

    @property
    def target_reached(self) -> bool:
        """Si el nuevo precio es menor o igual al precio objetivo."""
        return False  # Se setea externamente


class PriceUpdater:
    """
    Servicio de actualización de precios.

    Coordina repositorios, proveedores y caché para
    actualizar precios de forma eficiente.
    """

    def __init__(
        self,
        product_repo: ProductRepository,
        history_repo: HistoryRepository,
        provider_manager: ProviderManager,
        cache: PriceCache,
    ) -> None:
        self._products = product_repo
        self._history = history_repo
        self._providers = provider_manager
        self._cache = cache

    def update_single(
        self,
        product_id: int,
        headless: bool = True,
        use_cache: bool = True,
    ) -> UpdateResult | None:
        """
        Actualiza el precio de un producto individual.

        Args:
            product_id: ID del producto a actualizar.
            headless: Ejecutar navegador en segundo plano.
            use_cache: Usar caché si está disponible.

        Returns:
            UpdateResult con el resultado de la operación.
        """
        product = self._products.get_by_id(product_id)
        if not product:
            logger.warning("Producto no encontrado: id=%d", product_id)
            return None

        if use_cache:
            cached_price = self._cache.get(product.url)
            if cached_price is not None:
                logger.info(
                    "Usando precio cacheado para %s: %s",
                    product.name,
                    f"{cached_price:,.0f}",
                )
                return self._apply_price(product, cached_price)

        provider, price = self._providers.get_price(product.url, headless=headless)

        if price is not None:
            self._cache.set(product.url, price)
            return self._apply_price(product, price)
        else:
            logger.warning(
                "No se pudo actualizar precio: %s", product.name
            )
            return UpdateResult(
                product_id=product.id,
                product_name=product.name,
                old_price=product.current_price,
                new_price=None,
                success=False,
                error="No se pudo obtener el precio",
            )

    def update_all(
        self,
        headless: bool = True,
        use_cache: bool = True,
        callback: Optional[Callable[[int, int, str, bool], None]] = None,
    ) -> list[UpdateResult]:
        """
        Actualiza los precios de todos los productos activos.

        Args:
            headless: Ejecutar navegador en segundo plano.
            use_cache: Usar caché si está disponible.
            callback: Función de progreso (current, total, name, success).

        Returns:
            Lista de resultados de actualización.
        """
        products = self._products.get_all(active_only=True)
        total = len(products)
        results: list[UpdateResult] = []

        logger.info("Iniciando actualizacion masiva: %d productos", total)

        for i, product in enumerate(products):
            if i > 0:
                _time.sleep(3)

            if callback:
                callback(i + 1, total, product.name, False)

            result = self.update_single(
                product.id, headless=headless, use_cache=use_cache
            )
            if result:
                results.append(result)

            if callback:
                callback(i + 1, total, product.name, result.success if result else False)

        successful = sum(1 for r in results if r.success)
        logger.info(
            "Actualización masiva completada: %d/%d exitosas",
            successful,
            total,
        )
        return results

    def _apply_price(self, product: Product, new_price: float) -> UpdateResult:
        """Aplica un precio nuevo al producto y registra en historial."""
        old_price = product.current_price
        updated = self._products.update_price(product.id, new_price)

        if updated:
            self._history.add_record(product.id, new_price)

        return UpdateResult(
            product_id=product.id,
            product_name=product.name,
            old_price=old_price,
            new_price=new_price,
            success=True,
        )

    def check_target_prices(self) -> list[dict]:
        """
        Verifica qué productos alcanzaron su precio objetivo.

        Returns:
            Lista de dicts con producto, precio actual y objetivo.
        """
        alerts = []
        products = self._products.get_all(active_only=True)
        for product in products:
            if (
                product.target_price is not None
                and product.current_price is not None
                and product.current_price <= product.target_price
            ):
                alerts.append({
                    "product": product,
                    "current_price": product.current_price,
                    "target_price": product.target_price,
                })
                logger.info(
                    "Alerta de precio: %s alcanzó %s (objetivo: %s)",
                    product.name,
                    f"{product.current_price:,.0f}",
                    f"{product.target_price:,.0f}",
                )
        return alerts

    def import_from_json(self) -> list[UpdateResult]:
        """
        Importa precios desde data/prices.json (generado por excel_to_json.py).

        Actualiza el precio de cada producto en la BD cuya URL coincida con una
        entrada del JSON. Retorna lista de resultados.
        """
        json_path = Path(__file__).parent.parent / "data" / "prices.json"
        if not json_path.exists():
            logger.warning("Archivo JSON no encontrado: %s", json_path)
            return []

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Error leyendo JSON: %s", e)
            return []

        url_to_price = {}
        for item in data:
            url = item.get("url", "")
            price = item.get("price")
            if url and price is not None:
                url_to_price[url] = float(price)

        if not url_to_price:
            logger.warning("JSON sin precios")
            return []

        products = self._products.get_all(active_only=True)
        results: list[UpdateResult] = []

        for product in products:
            if product.url and product.url in url_to_price:
                new_price = url_to_price[product.url]
                result = self._apply_price(product, new_price)
                results.append(result)
                logger.info(
                    "Importado: %s = %s",
                    product.name,
                    f"{new_price:,.0f}",
                )
            elif product.name:
                name_lower = product.name.lower()
                for item in data:
                    item_name = item.get("name", "").lower()
                    if item_name and item_name in name_lower or name_lower in item_name:
                        new_price = float(item["price"])
                        result = self._apply_price(product, new_price)
                        results.append(result)
                        logger.info(
                            "Importado (nombre): %s = %s",
                            product.name,
                            f"{new_price:,.0f}",
                        )
                        break

        imported = sum(1 for r in results if r.success)
        logger.info("Importacion JSON: %d/%d productos actualizados", imported, len(products))
        return results
