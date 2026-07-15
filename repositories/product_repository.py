"""
PC Parts Tracker - Repositorio de Productos

Capa de abstracción para operaciones CRUD de productos.
Permite cambiar de SQLite a cualquier otro backend sin romper la app.
"""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database.models import Product
from utils.logger import get_logger

logger = get_logger("repositories.product")


class ProductRepository:
    """Repositorio para operaciones con la tabla de productos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self, active_only: bool = True) -> list[Product]:
        """Obtiene todos los productos."""
        stmt = select(Product)
        if active_only:
            stmt = stmt.where(Product.active == True)
        stmt = stmt.order_by(Product.category, Product.name)
        result = self._session.execute(stmt)
        products = list(result.scalars().all())
        logger.debug("Obtenidos %d productos", len(products))
        return products

    def get_by_id(self, product_id: int) -> Product | None:
        """Obtiene un producto por su ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_category(self, category: str) -> list[Product]:
        """Obtiene productos filtrados por categoría."""
        stmt = (
            select(Product)
            .where(Product.category == category, Product.active == True)
            .order_by(Product.name)
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def search(self, query: str) -> list[Product]:
        """Busca productos por nombre, marca o modelo."""
        pattern = f"%{query}%"
        stmt = (
            select(Product)
            .where(
                Product.active == True,
                (
                    (Product.name.ilike(pattern))
                    | (Product.brand.ilike(pattern))
                    | (Product.model.ilike(pattern))
                ),
            )
            .order_by(Product.name)
        )
        result = self._session.execute(stmt)
        products = list(result.scalars().all())
        logger.debug("Búsqueda '%s': %d resultados", query, len(products))
        return products

    def get_categories(self) -> list[str]:
        """Obtiene la lista de categorías únicas existentes."""
        stmt = (
            select(Product.category)
            .where(Product.active == True)
            .distinct()
            .order_by(Product.category)
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def add(self, product: Product) -> Product:
        """Agrega un nuevo producto."""
        self._session.add(product)
        self._session.commit()
        self._session.refresh(product)
        logger.info("Producto creado: %s (id=%d)", product.name, product.id)
        return product

    def update(self, product: Product) -> Product:
        """Actualiza un producto existente."""
        self._session.commit()
        self._session.refresh(product)
        logger.info("Producto actualizado: %s (id=%d)", product.name, product.id)
        return product

    def update_price(self, product_id: int, new_price: float) -> Product | None:
        """
        Actualiza el precio de un producto y gestiona precios histórico.

        Args:
            product_id: ID del producto.
            new_price: Nuevo precio.

        Returns:
            Producto actualizado o None si no se encontró.
        """
        product = self.get_by_id(product_id)
        if not product:
            logger.warning("Producto no encontrado: id=%d", product_id)
            return None

        product.previous_price = product.current_price
        product.current_price = new_price
        product.last_updated = datetime.now()

        if product.lowest_price is None or new_price < product.lowest_price:
            product.lowest_price = new_price
            logger.info(
                "Nuevo mínimo histórico para %s: %s",
                product.name,
                f"{new_price:,.0f}",
            )

        if product.highest_price is None or new_price > product.highest_price:
            product.highest_price = new_price

        self._session.commit()
        self._session.refresh(product)
        logger.info(
            "Precio actualizado: %s | %s -> %s",
            product.name,
            f"{product.previous_price:,.0f}" if product.previous_price else "N/A",
            f"{new_price:,.0f}",
        )
        return product

    def delete(self, product_id: int) -> bool:
        """
        Elimina un producto (soft delete: marca como inactivo).

        Returns:
            True si se eliminó, False si no se encontró.
        """
        product = self.get_by_id(product_id)
        if not product:
            return False
        product.active = False
        self._session.commit()
        logger.info("Producto desactivado: %s (id=%d)", product.name, product_id)
        return True

    def hard_delete(self, product_id: int) -> bool:
        """Elimina permanentemente un producto."""
        product = self.get_by_id(product_id)
        if not product:
            return False
        name = product.name
        self._session.delete(product)
        self._session.commit()
        logger.info("Producto eliminado permanentemente: %s (id=%d)", name, product_id)
        return True

    def count(self, active_only: bool = True) -> int:
        """Cuenta el número total de productos."""
        stmt = select(func.count(Product.id))
        if active_only:
            stmt = stmt.where(Product.active == True)
        return self._session.execute(stmt).scalar_one()
