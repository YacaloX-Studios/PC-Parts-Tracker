"""
PC Parts Tracker - Proveedor Base (Abstracto)

Define la interfaz abstracta que todos los proveedores deben implementar.
Para agregar una nueva tienda, solo hereda de esta clase.
"""

from abc import ABC, abstractmethod


class Provider(ABC):
    """
    Interfaz abstracta para proveedores de precios.

    Cada tienda online debe implementar esta clase con su lógica
    específica de scraping.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del proveedor (ej: 'MercadoLibre')."""
        ...

    @abstractmethod
    def matches_url(self, url: str) -> bool:
        """
        Determina si una URL pertenece a este proveedor.

        Args:
            url: URL del producto.

        Returns:
            True si la URL corresponde a este proveedor.
        """
        ...

    @abstractmethod
    def get_price(self, url: str, headless: bool = True) -> float | None:
        """
        Obtiene el precio de un producto desde su URL.

        Args:
            url: URL del producto.
            headless: Si es True, ejecuta el navegador en segundo plano.

        Returns:
            Precio como float o None si falló.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
