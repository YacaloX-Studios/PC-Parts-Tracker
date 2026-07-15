"""
PC Parts Tracker - Repositorio de Builds (PCs Completas)

Operaciones CRUD para configuraciones de PC completas.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database.models import Build, BuildItem, Product
from utils.logger import get_logger

logger = get_logger("repositories.build")


class BuildRepository:
    """Repositorio para operaciones con builds/PCs completas."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> list[Build]:
        """Obtiene todos los builds con sus items."""
        stmt = select(Build).options(joinedload(Build.items)).order_by(Build.name)
        result = self._session.execute(stmt)
        return list(result.unique().scalars().all())

    def get_by_id(self, build_id: int) -> Build | None:
        """Obtiene un build por su ID con sus items cargados."""
        stmt = (
            select(Build)
            .options(joinedload(Build.items))
            .where(Build.id == build_id)
        )
        result = self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def create_build(self, name: str, product_ids: list[int]) -> Build:
        """
        Crea un nuevo build con los productos especificados.

        Args:
            name: Nombre del build (ej: "PC Gamer PAPÁ™").
            product_ids: Lista de IDs de productos a incluir.

        Returns:
            Build creado.
        """
        build = Build(name=name)
        for pid in product_ids:
            build.items.append(BuildItem(product_id=pid))
        self._session.add(build)
        self._session.commit()
        self._session.refresh(build)
        logger.info(
            "Build creado: '%s' con %d productos", name, len(product_ids)
        )
        return build

    def add_product(self, build_id: int, product_id: int) -> BuildItem | None:
        """Agrega un producto a un build existente."""
        build = self.get_by_id(build_id)
        if not build:
            return None
        existing = any(item.product_id == product_id for item in build.items)
        if existing:
            logger.warning(
                "Producto ya existe en build: build=%s, product_id=%d",
                build.name,
                product_id,
            )
            return None
        item = BuildItem(build_id=build_id, product_id=product_id)
        self._session.add(item)
        self._session.commit()
        self._session.refresh(item)
        logger.info(
            "Producto agregado a build: build='%s', product_id=%d",
            build.name,
            product_id,
        )
        return item

    def remove_product(self, build_id: int, product_id: int) -> bool:
        """Remueve un producto de un build."""
        stmt = select(BuildItem).where(
            BuildItem.build_id == build_id,
            BuildItem.product_id == product_id,
        )
        result = self._session.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            return False
        self._session.delete(item)
        self._session.commit()
        logger.info(
            "Producto removido de build: build_id=%d, product_id=%d",
            build_id,
            product_id,
        )
        return True

    def get_build_total(self, build_id: int) -> dict:
        """
        Calcula el total de un build con precios actuales y mínimos.

        Returns:
            Dict con items, total_current, total_lowest, possible_savings.
        """
        build = self.get_by_id(build_id)
        if not build:
            return {"items": [], "total_current": 0, "total_lowest": 0, "possible_savings": 0}

        items_data = []
        total_current = 0.0
        total_lowest = 0.0

        for item in build.items:
            product = self._session.get(Product, item.product_id)
            if product:
                current = product.current_price or 0
                lowest = product.lowest_price or current
                total_current += current
                total_lowest += lowest
                items_data.append({
                    "product_id": product.id,
                    "name": product.display_name,
                    "category": product.category,
                    "current_price": current,
                    "lowest_price": lowest,
                    "currency": product.currency,
                })

        return {
            "items": items_data,
            "total_current": total_current,
            "total_lowest": total_lowest,
            "possible_savings": total_current - total_lowest,
        }

    def update_name(self, build_id: int, new_name: str) -> bool:
        """Renombra un build."""
        build = self.get_by_id(build_id)
        if not build:
            return False
        old_name = build.name
        build.name = new_name
        self._session.commit()
        logger.info("Build renombrado: '%s' -> '%s'", old_name, new_name)
        return True

    def delete_build(self, build_id: int) -> bool:
        """Elimina un build y sus items."""
        build = self.get_by_id(build_id)
        if not build:
            return False
        name = build.name
        self._session.delete(build)
        self._session.commit()
        logger.info("Build eliminado: '%s' (id=%d)", name, build_id)
        return True
