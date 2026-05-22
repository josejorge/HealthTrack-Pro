"""
Sistema de logging profesional para HealthTrack Pro.

Configura múltiples handlers: consola (debug) y archivo rotativo (producción).
Todos los mensajes se emiten en español.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configurar_logger(
    nombre: str = "healthtrack",
    nivel_consola: int = logging.DEBUG,
    nivel_archivo: int = logging.INFO,
    directorio_logs: Path | None = None,
) -> logging.Logger:
    """
    Inicializa y devuelve el logger principal de la aplicación.

    Args:
        nombre: Nombre del logger.
        nivel_consola: Nivel mínimo para la salida en consola.
        nivel_archivo: Nivel mínimo para escritura en archivo.
        directorio_logs: Ruta donde se guardarán los logs. Se crea si no existe.

    Returns:
        Logger configurado listo para usar.
    """
    logger = logging.getLogger(nombre)

    # Evitar duplicar handlers si ya fue configurado
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de consola
    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setLevel(nivel_consola)
    handler_consola.setFormatter(formato)
    logger.addHandler(handler_consola)

    # Handler de archivo rotativo
    if directorio_logs is None:
        directorio_logs = Path(__file__).parent.parent / "logs"

    directorio_logs.mkdir(parents=True, exist_ok=True)
    ruta_log = directorio_logs / "healthtrack.log"

    handler_archivo = RotatingFileHandler(
        filename=ruta_log,
        maxBytes=5 * 1024 * 1024,  # 5 MB por archivo
        backupCount=5,
        encoding="utf-8",
    )
    handler_archivo.setLevel(nivel_archivo)
    handler_archivo.setFormatter(formato)
    logger.addHandler(handler_archivo)

    # Handler de errores en archivo separado
    ruta_errores = directorio_logs / "errores.log"
    handler_errores = RotatingFileHandler(
        filename=ruta_errores,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler_errores.setLevel(logging.ERROR)
    handler_errores.setFormatter(formato)
    logger.addHandler(handler_errores)

    logger.info("Sistema de logging inicializado correctamente")
    return logger


def obtener_logger(nombre: str) -> logging.Logger:
    """
    Obtiene un logger hijo del logger principal.

    Útil para que cada módulo tenga su propio nombre visible en los logs.

    Args:
        nombre: Sub-nombre del logger (ej. 'healthtrack.services.registro').

    Returns:
        Logger hijo configurado.
    """
    return logging.getLogger(f"healthtrack.{nombre}")


# Logger raíz de la aplicación — importar desde otros módulos
logger = configurar_logger()
