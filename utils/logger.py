"""
PC Parts Tracker - Sistema de Logging

Configura logging rotativo con archivos y consola.
En modo developer, muestra logs DEBUG en consola.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logger(developer_mode: bool = False) -> logging.Logger:
    """
    Configura y retorna el logger principal de la aplicación.

    Args:
        developer_mode: Si es True, muestra logs DEBUG en consola.

    Returns:
        Logger configurado.
    """
    logger = logging.getLogger("pc_parts_tracker")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if developer_mode else logging.INFO)
    console_formatter = logging.Formatter(
        "%(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("Logger inicializado (developer_mode=%s)", developer_mode)
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger hijo para un módulo específico.

    Args:
        name: Nombre del módulo (ej: 'database', 'providers.mercadolibre').

    Returns:
        Logger hijo del logger principal.
    """
    return logging.getLogger(f"pc_parts_tracker.{name}")
