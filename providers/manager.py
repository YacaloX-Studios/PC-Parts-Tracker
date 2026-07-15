"""
PC Parts Tracker - Gestor de Proveedores

Detecta automáticamente qué proveedor usar según la URL del producto.
Registra y gestiona todos los proveedores disponibles.
"""

from providers.base import Provider
from utils.logger import get_logger

logger = get_logger("providers.manager")


class ProviderManager:
    """
    Gestor central de proveedores.

    Detecta la tienda a partir de una URL y delega la obtención
    del precio al proveedor correspondiente.
    """

    def __init__(self) -> None:
        self._providers: list[Provider] = []

    def register(self, provider: Provider) -> None:
        """
        Registra un nuevo proveedor.

        Args:
            provider: Instancia de un proveedor.
        """
        self._providers.append(provider)
        logger.info("Proveedor registrado: %s", provider.name)

    def detect_provider(self, url: str) -> Provider | None:
        """
        Detecta qué proveedor corresponde a una URL.

        Args:
            url: URL del producto.

        Returns:
            Proveedor correspondiente o None si ninguno coincide.
        """
        for provider in self._providers:
            if provider.matches_url(url):
                logger.debug(
                    "Proveedor detectado para URL: %s -> %s",
                    url,
                    provider.name,
                )
                return provider
        logger.warning("No se encontró proveedor para URL: %s", url)
        return None

    def get_price(self, url: str, headless: bool = True) -> tuple[Provider | None, float | None]:
        """
        Obtiene el precio de una URL usando el proveedor adecuado.

        Args:
            url: URL del producto.
            headless: Si es True, ejecuta el navegador en segundo plano.

        Returns:
            Tupla de (proveedor, precio) o (None, None) si falló.
        """
        provider = self.detect_provider(url)
        if not provider:
            return None, None

        try:
            price = provider.get_price(url, headless=headless)
            if price is not None:
                logger.info(
                    "Precio obtenido: %s -> %s %s",
                    provider.name,
                    f"{price:,.0f}",
                    url,
                )
            else:
                logger.warning(
                    "No se pudo obtener precio: %s | %s",
                    provider.name,
                    url,
                )
            return provider, price
        except Exception as e:
            logger.error(
                "Error obteniendo precio de %s: %s", provider.name, str(e)
            )
            return provider, None

    @property
    def providers(self) -> list[Provider]:
        """Lista de proveedores registrados."""
        return self._providers.copy()

    @property
    def provider_names(self) -> list[str]:
        """Nombres de los proveedores registrados."""
        return [p.name for p in self._providers]
