"""
PC Parts Tracker - Gestión de Configuración

Carga y guarda el archivo config.json con valores por defecto.
"""

import json
import os
from pathlib import Path
from typing import Any

from utils.logger import get_logger
from pcbuilding_core.enums import ComponentCategory

logger = get_logger("config")

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

DEFAULTS: dict[str, Any] = {
    "appearance_mode": "dark",
    "color_theme": "blue",
    "browser_headless": True,
    "cache_ttl_minutes": 60,
    "default_currency": "COP",
    "developer_mode": False,
    "backup_on_exit": True,
    "window_width": 1200,
    "window_height": 700,
    "categories": [c.value for c in ComponentCategory],
}


class AppConfig:
    """Gestor de configuración de la aplicación."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._path = config_path or CONFIG_PATH
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Carga la configuración desde disco. Si no existe, crea una con defaults."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                for key, value in DEFAULTS.items():
                    if key not in self._data:
                        self._data[key] = value
                logger.info("Configuración cargada desde %s", self._path)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Error leyendo config.json: %s. Usando defaults.", e)
                self._data = DEFAULTS.copy()
        else:
            self._data = DEFAULTS.copy()
            self.save()
            logger.info("Configuración por defecto creada en %s", self._path)

    def save(self) -> None:
        """Guarda la configuración actual a disco."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug("Configuración guardada")
        except OSError as e:
            logger.error("Error guardando config.json: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Establece un valor y guarda."""
        self._data[key] = value
        self.save()

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    @property
    def appearance_mode(self) -> str:
        return self._data.get("appearance_mode", "dark")

    @property
    def color_theme(self) -> str:
        return self._data.get("color_theme", "blue")

    @property
    def browser_headless(self) -> bool:
        return self._data.get("browser_headless", True)

    @property
    def cache_ttl_minutes(self) -> int:
        return self._data.get("cache_ttl_minutes", 60)

    @property
    def developer_mode(self) -> bool:
        return self._data.get("developer_mode", False)

    @property
    def backup_on_exit(self) -> bool:
        return self._data.get("backup_on_exit", True)

    @property
    def categories(self) -> list[str]:
        return self._data.get("categories", DEFAULTS["categories"])
