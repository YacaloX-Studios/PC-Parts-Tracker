"""
PC Parts Tracker - Servicio de Builds (PCs Completas)

Lógica de negocio para configuraciones de PC completas:
totales, ahorro posible, comparación de precios.
"""

from repositories.build_repository import BuildRepository
from repositories.product_repository import ProductRepository
from utils.logger import get_logger

logger = get_logger("services.build")


class BuildService:
    """Servicio de lógica para builds/PCs completas."""

    def __init__(
        self,
        build_repo: BuildRepository,
        product_repo: ProductRepository,
    ) -> None:
        self._builds = build_repo
        self._products = product_repo

    def get_build_summary(self, build_id: int) -> dict | None:
        """
        Obtiene el resumen completo de un build.

        Returns:
            Dict con nombre, items, totales y ahorro posible.
        """
        build = self._builds.get_by_id(build_id)
        if not build:
            return None

        totals = self._builds.get_build_total(build_id)
        return {
            "id": build.id,
            "name": build.name,
            "created_at": build.created_at,
            "items": totals["items"],
            "total_current": totals["total_current"],
            "total_lowest": totals["total_lowest"],
            "possible_savings": totals["possible_savings"],
            "item_count": len(totals["items"]),
        }

    def get_all_builds_summary(self) -> list[dict]:
        """Obtiene un resumen de todos los builds."""
        builds = self._builds.get_all()
        summaries = []
        for build in builds:
            totals = self._builds.get_build_total(build.id)
            summaries.append({
                "id": build.id,
                "name": build.name,
                "item_count": len(totals["items"]),
                "total_current": totals["total_current"],
                "total_lowest": totals["total_lowest"],
                "possible_savings": totals["possible_savings"],
            })
        return summaries

    def create_build(self, name: str, product_ids: list[int]) -> dict | None:
        """
        Crea un nuevo build.

        Args:
            name: Nombre del build.
            product_ids: IDs de productos a incluir.

        Returns:
            Resumen del build creado.
        """
        if not product_ids:
            logger.warning("Intento de build vacío: '%s'", name)
            return None

        build = self._builds.create_build(name, product_ids)
        return self.get_build_summary(build.id)

    def add_product_to_build(self, build_id: int, product_id: int) -> bool:
        """Agrega un producto a un build existente."""
        item = self._builds.add_product(build_id, product_id)
        if item:
            logger.info(
                "Producto agregado al build %d: producto %d",
                build_id,
                product_id,
            )
            return True
        return False

    def remove_product_from_build(self, build_id: int, product_id: int) -> bool:
        """Remueve un producto de un build."""
        return self._builds.remove_product(build_id, product_id)

    def delete_build(self, build_id: int) -> bool:
        """Elimina un build."""
        return self._builds.delete_build(build_id)

    def format_build_display(self, build_id: int) -> str:
        """
        Genera el texto formateado de un build para mostrar en GUI.

        Returns:
            Texto tipo:
            PC Gamer PAPÁ™
            ─────────────────────────
            GPU     ASUS RTX 5060          $1.700.000
            CPU     Ryzen 5 7500F          $487.770
            ─────────────────────────
            TOTAL                       $4.500.000
        """
        summary = self.get_build_summary(build_id)
        if not summary:
            return "Build no encontrado"

        lines = [summary["name"], "─" * 50]

        for item in summary["items"]:
            cat = item["category"].ljust(12)
            name = item["name"][:25].ljust(25)
            price = f"${item['current_price']:,.0f}"
            lines.append(f"{cat}{name}{price:>15}")

        lines.append("─" * 50)
        lines.append(
            f"{'TOTAL':<37}${summary['total_current']:>13,.0f}"
        )

        if summary["possible_savings"] > 0:
            lines.append(
                f"{'Ahorro posible':<37}${summary['possible_savings']:>13,.0f}"
            )

        return "\n".join(lines)
