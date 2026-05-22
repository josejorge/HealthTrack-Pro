"""
Gestor de temas visuales (oscuro / claro) de HealthTrack Pro.

Genera y aplica hojas de estilo QSS dinámicamente según el tema activo.
Expone señales Qt para que los widgets reaccionen a cambios de tema.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from core.config import config
from core.constants import COLORES_CLARO, COLORES_OSCURO

logger = logging.getLogger("healthtrack.widgets.theme")


def _generar_qss(colores: dict[str, str]) -> str:
    """Genera el stylesheet completo de la aplicación a partir de la paleta de colores."""
    c = colores
    return f"""
/* ─── Base Global ──────────────────────────────────── */
* {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
    color: {c['texto_primario']};
}}

QMainWindow, QWidget#central_widget, QStackedWidget {{
    background-color: {c['fondo_principal']};
}}

QDialog {{
    background-color: {c['fondo_principal']};
}}

/* ─── Sidebar ───────────────────────────────────────── */
QWidget#sidebar {{
    background-color: {c['sidebar_fondo']};
    border-right: 1px solid {c['borde']};
}}

QLabel#logo_label {{
    color: #6366f1;
    font-size: 20px;
    font-weight: 700;
    padding: 8px 0px;
}}

QLabel#sidebar_version {{
    color: {c['texto_deshabilitado']};
    font-size: 10px;
}}

/* ─── Botones de navegación ─────────────────────────── */
QPushButton#nav_btn {{
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: left;
    color: {c['texto_secundario']};
    font-size: 13px;
    font-weight: 500;
}}

QPushButton#nav_btn:hover {{
    background-color: {c['sidebar_item_hover']};
    color: {c['texto_primario']};
}}

QPushButton#nav_btn[activo="true"] {{
    background-color: #6366f1;
    color: #ffffff;
    font-weight: 600;
}}

/* ─── Tarjetas de métricas ──────────────────────────── */
QFrame#metric_card {{
    background-color: {c['fondo_tarjeta']};
    border: 1px solid {c['borde']};
    border-radius: 14px;
    padding: 4px;
}}

QFrame#metric_card:hover {{
    border: 1px solid {c['acento']};
}}

QLabel#card_titulo {{
    color: {c['texto_secundario']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel#card_valor {{
    color: {c['texto_primario']};
    font-size: 28px;
    font-weight: 700;
}}

QLabel#card_unidad {{
    color: {c['texto_secundario']};
    font-size: 13px;
    font-weight: 400;
}}

QLabel#card_tendencia {{
    font-size: 12px;
    font-weight: 500;
}}

/* ─── Encabezados y títulos ─────────────────────────── */
QLabel#titulo_seccion {{
    color: {c['texto_primario']};
    font-size: 20px;
    font-weight: 700;
}}

QLabel#subtitulo_seccion {{
    color: {c['texto_secundario']};
    font-size: 13px;
}}

QLabel#etiqueta_campo {{
    color: {c['texto_secundario']};
    font-size: 12px;
    font-weight: 600;
}}

/* ─── Inputs y formularios ──────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['fondo_input']};
    border: 1.5px solid {c['borde']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {c['texto_primario']};
    selection-background-color: #6366f1;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1.5px solid {c['borde_focus']};
    background-color: {c['fondo_secundario']};
}}

QLineEdit:disabled, QTextEdit:disabled {{
    color: {c['texto_deshabilitado']};
    background-color: {c['fondo_principal']};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {c['fondo_input']};
    border: 1.5px solid {c['borde']};
    border-radius: 8px;
    padding: 7px 10px;
    color: {c['texto_primario']};
    min-width: 80px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1.5px solid {c['borde_focus']};
}}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {c['borde']};
    border: none;
    width: 18px;
    border-radius: 4px;
}}

QComboBox {{
    background-color: {c['fondo_input']};
    border: 1.5px solid {c['borde']};
    border-radius: 8px;
    padding: 7px 12px;
    color: {c['texto_primario']};
    min-width: 120px;
}}

QComboBox:focus {{
    border: 1.5px solid {c['borde_focus']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['fondo_secundario']};
    border: 1px solid {c['borde']};
    border-radius: 8px;
    selection-background-color: {c['acento']};
    color: {c['texto_primario']};
    padding: 4px;
}}

QSlider::groove:horizontal {{
    background-color: {c['borde']};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: #6366f1;
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: -6px 0;
}}

QSlider::sub-page:horizontal {{
    background-color: #6366f1;
    border-radius: 3px;
}}

/* ─── Botones ───────────────────────────────────────── */
QPushButton {{
    background-color: {c['borde']};
    color: {c['texto_primario']};
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {c['texto_deshabilitado']};
}}

QPushButton#btn_primario {{
    background-color: #6366f1;
    color: #ffffff;
    font-weight: 600;
    padding: 10px 24px;
}}

QPushButton#btn_primario:hover {{
    background-color: #4f46e5;
}}

QPushButton#btn_primario:pressed {{
    background-color: #4338ca;
}}

QPushButton#btn_secundario {{
    background-color: transparent;
    color: #6366f1;
    border: 1.5px solid #6366f1;
    font-weight: 600;
    padding: 9px 18px;
}}

QPushButton#btn_secundario:hover {{
    background-color: rgba(99, 102, 241, 0.1);
}}

QPushButton#btn_peligro {{
    background-color: #ef4444;
    color: #ffffff;
    font-weight: 600;
}}

QPushButton#btn_peligro:hover {{
    background-color: #dc2626;
}}

QPushButton:disabled {{
    background-color: {c['borde']};
    color: {c['texto_deshabilitado']};
}}

/* ─── Barra de título personalizada ─────────────────── */
QWidget#barra_titulo {{
    background-color: {c['fondo_principal']};
    border-bottom: 1px solid {c['borde']};
}}

/* ─── Scrollbars ────────────────────────────────────── */
QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {c['scrollbar']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c['scrollbar_hover']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background-color: {c['scrollbar']};
    border-radius: 4px;
}}

/* ─── Separadores ───────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {c['borde']};
}}

/* ─── Tablas / Listas ───────────────────────────────── */
QTableWidget, QListWidget, QTreeWidget {{
    background-color: {c['fondo_secundario']};
    border: 1px solid {c['borde']};
    border-radius: 10px;
    gridline-color: {c['borde']};
    color: {c['texto_primario']};
    alternate-background-color: {c['fondo_principal']};
}}

QTableWidget::item:selected, QListWidget::item:selected {{
    background-color: rgba(99, 102, 241, 0.2);
    color: {c['texto_primario']};
}}

QHeaderView::section {{
    background-color: {c['fondo_principal']};
    color: {c['texto_secundario']};
    border: none;
    border-bottom: 1px solid {c['borde']};
    padding: 8px;
    font-size: 11px;
    font-weight: 600;
}}

/* ─── Calendarios ───────────────────────────────────── */
QCalendarWidget {{
    background-color: {c['fondo_secundario']};
    color: {c['texto_primario']};
    border: 1px solid {c['borde']};
    border-radius: 12px;
}}

QCalendarWidget QAbstractItemView {{
    background-color: {c['fondo_secundario']};
    color: {c['texto_primario']};
    selection-background-color: #6366f1;
}}

QCalendarWidget QToolButton {{
    background-color: transparent;
    color: {c['texto_primario']};
    border: none;
    font-weight: 600;
}}

/* ─── Tooltips ──────────────────────────────────────── */
QToolTip {{
    background-color: {c['fondo_secundario']};
    color: {c['texto_primario']};
    border: 1px solid {c['borde']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ─── Checkboxes ────────────────────────────────────── */
QCheckBox {{
    color: {c['texto_primario']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1.5px solid {c['borde']};
    border-radius: 4px;
    background-color: {c['fondo_input']};
}}

QCheckBox::indicator:checked {{
    background-color: #6366f1;
    border-color: #6366f1;
}}

/* ─── GroupBox ──────────────────────────────────────── */
QGroupBox {{
    color: {c['texto_secundario']};
    border: 1px solid {c['borde']};
    border-radius: 10px;
    margin-top: 16px;
    padding-top: 8px;
    font-size: 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
}}

/* ─── Status Bar ────────────────────────────────────── */
QStatusBar {{
    background-color: {c['fondo_principal']};
    color: {c['texto_secundario']};
    border-top: 1px solid {c['borde']};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ─── Progress Bar ──────────────────────────────────── */
QProgressBar {{
    background-color: {c['borde']};
    border-radius: 6px;
    text-align: center;
    color: {c['texto_primario']};
    font-size: 11px;
    height: 12px;
    border: none;
}}

QProgressBar::chunk {{
    background-color: #6366f1;
    border-radius: 6px;
}}

/* ─── Alertas ───────────────────────────────────────── */
QFrame#alerta_normal {{
    background-color: rgba(34, 197, 94, 0.12);
    border: 1px solid rgba(34, 197, 94, 0.4);
    border-radius: 10px;
    padding: 4px;
}}

QFrame#alerta_atencion {{
    background-color: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 10px;
    padding: 4px;
}}

QFrame#alerta_preocupante {{
    background-color: rgba(249, 115, 22, 0.12);
    border: 1px solid rgba(249, 115, 22, 0.4);
    border-radius: 10px;
    padding: 4px;
}}

QFrame#alerta_critico {{
    background-color: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.5);
    border-radius: 10px;
    padding: 4px;
}}

/* ─── Área de gráficas ──────────────────────────────── */
QWidget#chart_container {{
    background-color: {c['fondo_tarjeta']};
    border: 1px solid {c['borde']};
    border-radius: 14px;
}}
"""


class GestorTema(QObject):
    """
    Singleton que gestiona el tema visual de la aplicación.

    Emite la señal `tema_cambiado` cuando el usuario alterna entre modos.
    """

    tema_cambiado = Signal(str)  # "oscuro" | "claro"
    _instancia: "GestorTema | None" = None

    def __new__(cls) -> "GestorTema":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def __init__(self) -> None:
        if not hasattr(self, "_inicializado"):
            super().__init__()
            self._tema_actual: str = config.tema
            self._inicializado = True

    @property
    def tema_actual(self) -> str:
        return self._tema_actual

    @property
    def es_oscuro(self) -> bool:
        return self._tema_actual == "oscuro"

    @property
    def colores(self) -> dict[str, str]:
        return COLORES_OSCURO if self.es_oscuro else COLORES_CLARO

    def aplicar_tema(self, nombre: str = "") -> None:
        """
        Aplica el tema indicado a toda la aplicación Qt.

        Args:
            nombre: "oscuro" o "claro". Si está vacío, usa el configurado.
        """
        if nombre:
            self._tema_actual = nombre

        app = QApplication.instance()
        if app is None:
            return

        qss = _generar_qss(self.colores)
        app.setStyleSheet(qss)
        config.tema = self._tema_actual
        self.tema_cambiado.emit(self._tema_actual)
        logger.debug("Tema aplicado: %s", self._tema_actual)

    def alternar(self) -> None:
        """Alterna entre modo oscuro y claro."""
        nuevo = "claro" if self.es_oscuro else "oscuro"
        self.aplicar_tema(nuevo)


# Instancia global
gestor_tema = GestorTema()
