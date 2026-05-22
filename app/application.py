"""
Clase Application — gestiona el ciclo de vida de HealthTrack Pro.

Inicializa la base de datos, aplica el tema y lanza la ventana principal.
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from core.config import config
from core.logger import configurar_logger
from database.connection import obtener_gestor
from widgets.theme_manager import gestor_tema
from core.constants import APP_NOMBRE, APP_VERSION

logger = logging.getLogger("healthtrack.app")


class Application:
    """
    Clase central de la aplicación.

    Responsabilidades:
    - Configurar el logger antes de cualquier otro módulo
    - Inicializar la base de datos (create_all)
    - Crear el QApplication con la fuente y metadatos correctos
    - Aplicar el tema inicial
    - Crear y mostrar la ventana principal
    - Ejecutar el bucle de eventos Qt
    """

    def __init__(self) -> None:
        # Logger debe configurarse antes de todos los imports de UI
        configurar_logger()
        logger.info("Iniciando %s v%s", APP_NOMBRE, APP_VERSION)

        # Inicializar base de datos
        gestor = obtener_gestor()
        if not gestor.verificar_conexion():
            logger.critical("No se pudo conectar a la base de datos")
            sys.exit(1)

        # Crear directorio de exports y backups si no existen
        config.exportacion_directorio.mkdir(parents=True, exist_ok=True)
        config.backup_directorio.mkdir(parents=True, exist_ok=True)

    def ejecutar(self) -> int:
        """Crea la app Qt, la ventana principal y ejecuta el loop de eventos."""
        app = QApplication.instance() or QApplication(sys.argv)

        # Metadatos de la aplicación
        app.setApplicationName(APP_NOMBRE)
        app.setApplicationVersion(APP_VERSION)
        app.setOrganizationName("HealthTrack")

        # Fuente por defecto
        fuente = QFont("Segoe UI", 13)
        app.setFont(fuente)

        # Aplicar tema inicial
        gestor_tema.aplicar_tema(config.tema)

        # Importar aquí para evitar imports circulares durante la init
        from ui.main_window import VentanaPrincipal
        ventana = VentanaPrincipal()
        ventana.show()

        logger.info("Ventana principal abierta")
        codigo_salida = app.exec()
        logger.info("Aplicación terminada con código %d", codigo_salida)
        return codigo_salida
