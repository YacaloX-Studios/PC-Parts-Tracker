"""
PC Parts Tracker - Sistema de Caché de Precios

Evita consultar MercadoLibre repetidamente.
Cachea precios con un TTL configurable (default: 60 minutos).
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("cache")

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_FILE = CACHE_DIR / "price_cache.json"


class PriceCache:
    """
    Caché de precios con TTL.

    Almacena precios obtenidos para no repetir scraping
    dentro del período de tiempo configurado.
    """

    def __init__(self, ttl_minutes: int = 60, cache_file: Path | None = None) -> None:
        """
        Args:
            ttl_minutes: Minutos de vida de cada entrada en caché.
            cache_file: Ruta al archivo JSON de caché.
        """
        self._ttl = timedelta(minutes=ttl_minutes)
        self._file = cache_file or CACHE_FILE
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        """Carga el caché desde disco."""
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                self._clean_expired()
                logger.debug("Caché cargado: %d entradas", len(self._data))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Error cargando caché: %s. Usando caché vacío.", e)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Guarda el caché a disco."""
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error("Error guardando caché: %s", e)

    def _clean_expired(self) -> None:
        """Elimina entradas expiradas del caché."""
        now = datetime.now()
        expired = [
            url
            for url, entry in self._data.items()
            if datetime.fromisoformat(entry["expires_at"]) <= now
        ]
        for url in expired:
            del self._data[url]
        if expired:
            logger.debug("Caché limpiado: %d entradas expiradas", len(expired))

    def get(self, url: str) -> float | None:
        """
        Obtiene un precio del caché si no ha expirado.

        Args:
            url: URL del producto.

        Returns:
            Precio cacheado o None si no existe o expiró.
        """
        self._clean_expired()
        entry = self._data.get(url)
        if not entry:
            return None

        expires_at = datetime.fromisoformat(entry["expires_at"])
        if expires_at <= datetime.now():
            del self._data[url]
            self._save()
            return None

        logger.debug(
            "Cache hit: %s -> %s",
            url[:60],
            f"{entry['price']:,.0f}",
        )
        return entry["price"]

    def set(self, url: str, price: float) -> None:
        """
        Almacena un precio en el caché.

        Args:
            url: URL del producto.
            price: Precio a cachear.
        """
        now = datetime.now()
        self._data[url] = {
            "price": price,
            "fetched_at": now.isoformat(),
            "expires_at": (now + self._ttl).isoformat(),
        }
        self._save()
        logger.debug(
            "Cache set: %s -> %s (expira: %s)",
            url[:60],
            f"{price:,.0f}",
            (now + self._ttl).strftime("%H:%M"),
        )

    def is_valid(self, url: str) -> bool:
        """Verifica si una URL tiene caché válido."""
        entry = self._data.get(url)
        if not entry:
            return False
        return datetime.fromisoformat(entry["expires_at"]) > datetime.now()

    def invalidate(self, url: str) -> bool:
        """Elimina una entrada del caché."""
        if url in self._data:
            del self._data[url]
            self._save()
            return True
        return False

    def clear(self) -> int:
        """Limpia todo el caché. Retorna número de entradas eliminadas."""
        count = len(self._data)
        self._data = {}
        self._save()
        logger.info("Caché limpiado completamente: %d entradas", count)
        return count

    @property
    def size(self) -> int:
        """Número de entradas en el caché."""
        return len(self._data)

    @property
    def stats(self) -> dict:
        """Estadísticas del caché."""
        self._clean_expired()
        return {
            "total_entries": len(self._data),
            "ttl_minutes": int(self._ttl.total_seconds() / 60),
        }
