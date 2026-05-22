"""
Sidebar de navegación lateral de HealthTrack Pro.

Muestra el logo, los ítems de navegación y el indicador
de alertas pendientes. Emite señal cuando el usuario selecciona
un módulo diferente.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from core.constants import APP_NOMBRE, APP_VERSION, ICONOS

logger = logging.getLogger("healthtrack.widgets.sidebar")

# Definición de ítems de navegación: (id_modulo, texto, icono, tooltip)
ITEMS_NAV = [
    ("dashboard",     "Dashboard",        "⊞",  "Vista principal y resumen del día"),
    ("registro",      "Nuevo Registro",   "✚",  "Registrar métricas de salud"),
    ("historial",     "Historial",        "📅", "Ver registros pasados"),
    ("estadisticas",  "Estadísticas",     "📊", "Gráficas y análisis"),
    ("alertas",       "Alertas",          "🔔", "Alertas y notificaciones de salud"),
]

ITEMS_INFERIORES = [
    ("configuracion", "Configuración",    "⚙",  "Ajustes de la aplicación"),
    ("ayuda",         "Ayuda",            "?",  "Documentación y soporte"),
]


class SidebarButton(QPushButton):
    """Botón de navegación de la sidebar con soporte para estado activo."""

    def __init__(self, id_modulo: str, texto: str, icono: str, tooltip: str) -> None:
        super().__init__()
        self.id_modulo = id_modulo
        self._activo = False

        self.setObjectName("nav_btn")
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(46)

        self._actualizar_texto(icono, texto, 0)

    def _actualizar_texto(self, icono: str, texto: str, conteo_alertas: int = 0) -> None:
        """Actualiza el texto visible con icono y, opcionalmente, badge de alertas."""
        self._icono = icono
        self._texto = texto
        badge = f"  ({conteo_alertas})" if conteo_alertas > 0 else ""
        self.setText(f"  {icono}   {texto}{badge}")

    def actualizar_badge(self, conteo: int) -> None:
        """Actualiza el badge de alertas en tiempo real."""
        self._actualizar_texto(self._icono, self._texto, conteo)

    @property
    def activo(self) -> bool:
        return self._activo

    @activo.setter
    def activo(self, valor: bool) -> None:
        self._activo = valor
        self.setProperty("activo", "true" if valor else "false")
        # Forzar re-evaluación del QSS
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QWidget):
    """
    Panel de navegación lateral.

    Señales:
        modulo_seleccionado(str): Emitida cuando el usuario cambia de módulo.
            El str es el id del módulo seleccionado.
    """

    modulo_seleccionado = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(230)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._botones: dict[str, SidebarButton] = {}
        self._modulo_activo: str = "dashboard"

        self._construir_ui()

    def _construir_ui(self) -> None:
        """Construye todos los elementos visuales de la sidebar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(4)

        # ── Logo ──────────────────────────────────
        layout.addWidget(self._crear_logo())
        layout.addSpacing(20)

        # ── Separador ─────────────────────────────
        layout.addWidget(self._crear_separador())
        layout.addSpacing(8)

        # ── Etiqueta sección ──────────────────────
        lbl_menu = QLabel("MENÚ PRINCIPAL")
        lbl_menu.setObjectName("sidebar_version")
        lbl_menu.setContentsMargins(8, 0, 0, 0)
        layout.addWidget(lbl_menu)
        layout.addSpacing(4)

        # ── Ítems principales ─────────────────────
        for id_mod, texto, icono, tooltip in ITEMS_NAV:
            btn = SidebarButton(id_mod, texto, icono, tooltip)
            btn.clicked.connect(lambda checked, m=id_mod: self._on_click(m))
            self._botones[id_mod] = btn
            layout.addWidget(btn)

        # ── Espaciador ────────────────────────────
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # ── Separador inferior ────────────────────
        layout.addWidget(self._crear_separador())
        layout.addSpacing(4)

        # ── Ítems inferiores ──────────────────────
        for id_mod, texto, icono, tooltip in ITEMS_INFERIORES:
            btn = SidebarButton(id_mod, texto, icono, tooltip)
            btn.clicked.connect(lambda checked, m=id_mod: self._on_click(m))
            self._botones[id_mod] = btn
            layout.addWidget(btn)

        layout.addSpacing(8)

        # ── Versión ───────────────────────────────
        lbl_version = QLabel(f"v{APP_VERSION}")
        lbl_version.setObjectName("sidebar_version")
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_version)

        # Activar dashboard por defecto
        self._activar(self._modulo_activo)

    def _crear_logo(self) -> QWidget:
        """Crea el área del logo con nombre de la app."""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(2)

        lbl_icono = QLabel("❤️‍🩺")
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fuente_icono = QFont()
        fuente_icono.setPointSize(24)
        lbl_icono.setFont(fuente_icono)

        lbl_nombre = QLabel(APP_NOMBRE)
        lbl_nombre.setObjectName("logo_label")

        lbl_slogan = QLabel("Tu salud, en tus manos")
        lbl_slogan.setObjectName("sidebar_version")

        layout.addWidget(lbl_icono)
        layout.addWidget(lbl_nombre)
        layout.addWidget(lbl_slogan)
        return contenedor

    def _crear_separador(self) -> QFrame:
        """Crea una línea separadora horizontal."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        return sep

    def _on_click(self, id_modulo: str) -> None:
        """Maneja el clic en un ítem de navegación."""
        if id_modulo == self._modulo_activo:
            return
        self._activar(id_modulo)
        self.modulo_seleccionado.emit(id_modulo)
        logger.debug("Módulo seleccionado: %s", id_modulo)

    def _activar(self, id_modulo: str) -> None:
        """Actualiza el estado visual del botón activo."""
        for id_mod, btn in self._botones.items():
            btn.activo = (id_mod == id_modulo)
        self._modulo_activo = id_modulo

    def activar_modulo(self, id_modulo: str) -> None:
        """Activa un módulo programáticamente (desde fuera del sidebar)."""
        self._activar(id_modulo)

    def actualizar_badge_alertas(self, conteo: int) -> None:
        """Actualiza el badge del botón de alertas."""
        if "alertas" in self._botones:
            self._botones["alertas"].actualizar_badge(conteo)
