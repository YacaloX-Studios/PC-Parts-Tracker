"""
PC Parts Tracker - Repositorio de Historial de Precios

Operaciones CRUD para el historial de precios de productos.
"""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database.models import PriceHistory
from utils.logger import get_logger

logger = get_logger("repositories.history")


class HistoryRepository:
    """Repositorio para operaciones con el historial de precios."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_record(self, product_id: int, price: float) -> PriceHistory:
        """
        Registra un nuevo punto en el historial de precios.

        Args:
            product_id: ID del producto.
            price: Precio registrado.

        Returns:
            Registro creado.
        """
        record = PriceHistory(
            product_id=product_id,
            price=price,
            date=datetime.now(),
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        logger.debug(
            "Historial registrado: producto_id=%d, precio=%s",
            product_id,
            f"{price:,.0f}",
        )
        return record

    def get_history(self, product_id: int) -> list[PriceHistory]:
        """
        Obtiene el historial completo de precios de un producto.

        Args:
            product_id: ID del producto.

        Returns:
            Lista de registros ordenados por fecha descendente.
        """
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.date.desc())
        )
        result = self._session.execute(stmt)
        records = list(result.scalars().all())
        logger.debug(
            "Historial de producto_id=%d: %d registros", product_id, len(records)
        )
        return records

    def get_history_range(
        self, product_id: int, start_date: datetime, end_date: datetime
    ) -> list[PriceHistory]:
        """
        Obtiene el historial de precios en un rango de fechas.

        Args:
            product_id: ID del producto.
            start_date: Fecha inicio.
            end_date: Fecha fin.

        Returns:
            Lista de registros en el rango.
        """
        stmt = (
            select(PriceHistory)
            .where(
                PriceHistory.product_id == product_id,
                PriceHistory.date >= start_date,
                PriceHistory.date <= end_date,
            )
            .order_by(PriceHistory.date.asc())
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def get_min_price(self, product_id: int) -> float | None:
        """Obtiene el precio más bajo registrado para un producto."""
        stmt = select(func.min(PriceHistory.price)).where(
            PriceHistory.product_id == product_id
        )
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def get_max_price(self, product_id: int) -> float | None:
        """Obtiene el precio más alto registrado para un producto."""
        stmt = select(func.max(PriceHistory.price)).where(
            PriceHistory.product_id == product_id
        )
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def get_avg_price(self, product_id: int) -> float | None:
        """Obtiene el precio promedio registrado para un producto."""
        stmt = select(func.avg(PriceHistory.price)).where(
            PriceHistory.product_id == product_id
        )
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def get_latest_price(self, product_id: int) -> float | None:
        """Obtiene el precio más reciente registrado para un producto."""
        stmt = (
            select(PriceHistory.price)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.date.desc())
            .limit(1)
        )
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def delete_history(self, product_id: int) -> int:
        """
        Elimina todo el historial de un producto.

        Returns:
            Número de registros eliminados.
        """
        stmt = select(PriceHistory).where(PriceHistory.product_id == product_id)
        result = self._session.execute(stmt)
        records = list(result.scalars().all())
        count = len(records)
        for record in records:
            self._session.delete(record)
        self._session.commit()
        logger.info(
            "Historial eliminado: producto_id=%d, %d registros", product_id, count
        )
        return count
