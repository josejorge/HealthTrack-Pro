"""
Tarjeta de métrica individual para el Dashboard.

Muestra el nombre, valor actual, unidad, tendencia e indicador
de criticidad con color dinámico según el nivel de alerta.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.constants import (
    COLORES_CRITICIDAD,
    CRITICIDAD_NORMAL,
    ICONOS,
)


class TarjetaMetrica(QFrame):
    """
    Tarjeta visual para una métrica de salud.

    Muestra:
    - Nombre de la métrica (arriba a la izquierda)
    - Indicador de criticidad (círculo de color, arriba a la derecha)
    - Valor numérico grande (centro)
    - Unidad de medida (junto al valor)
    - Tendencia con flecha (abajo)
    - Fechas de máximo/mínimo histórico (abajo)
    """

    def __init__(
        self,
        titulo: str,
        unidad: str = "",
        valor: str = "—",
        criticidad: str = CRITICIDAD_NORMAL,
        tendencia: str = "estable",
        tendencia_pct: float = 0.0,
        subtexto: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("metric_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(160)
        self.setFixedHeight(140)

        self._titulo = titulo
        self._unidad = unidad

        self._construir_ui()
        self.actualizar(valor, criticidad, tendencia, tendencia_pct, subtexto)

    def _construir_ui(self) -> None:
        """Construye la estructura de la tarjeta."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 14, 18, 12)
        layout_principal.setSpacing(6)

        # ── Fila superior: título + indicador ─────
        fila_top = QHBoxLayout()
        fila_top.setSpacing(8)

        self._lbl_titulo = QLabel(self._titulo.upper())
        self._lbl_titulo.setObjectName("card_titulo")
        self._lbl_titulo.setWordWrap(False)

        self._lbl_indicador = QLabel("●")
        self._lbl_indicador.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        fila_top.addWidget(self._lbl_titulo, 1)
        fila_top.addWidget(self._lbl_indicador)

        # ── Fila central: valor + unidad ──────────
        fila_valor = QHBoxLayout()
        fila_valor.setSpacing(4)
        fila_valor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._lbl_valor = QLabel("—")
        self._lbl_valor.setObjectName("card_valor")
        self._lbl_valor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._lbl_unidad = QLabel(self._unidad)
        self._lbl_unidad.setObjectName("card_unidad")
        self._lbl_unidad.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        fila_valor.addWidget(self._lbl_valor)
        fila_valor.addWidget(self._lbl_unidad)
        fila_valor.addStretch()

        # ── Fila inferior: tendencia + subtexto ───
        fila_bottom = QHBoxLayout()
        fila_bottom.setSpacing(8)

        self._lbl_tendencia = QLabel()
        self._lbl_tendencia.setObjectName("card_tendencia")

        self._lbl_subtexto = QLabel()
        self._lbl_subtexto.setObjectName("card_titulo")
        self._lbl_subtexto.setAlignment(Qt.AlignmentFlag.AlignRight)

        fila_bottom.addWidget(self._lbl_tendencia, 1)
        fila_bottom.addWidget(self._lbl_subtexto)

        # ── Ensamblar ─────────────────────────────
        layout_principal.addLayout(fila_top)
        layout_principal.addLayout(fila_valor)
        layout_principal.addStretch()
        layout_principal.addLayout(fila_bottom)

    def actualizar(
        self,
        valor: str = "—",
        criticidad: str = CRITICIDAD_NORMAL,
        tendencia: str = "estable",
        tendencia_pct: float = 0.0,
        subtexto: str = "",
    ) -> None:
        """Actualiza todos los valores visuales de la tarjeta."""
        self._lbl_valor.setText(str(valor))

        # Color del indicador según criticidad
        color_hex = COLORES_CRITICIDAD.get(criticidad, COLORES_CRITICIDAD[CRITICIDAD_NORMAL])
        self._lbl_indicador.setStyleSheet(f"color: {color_hex}; font-size: 14px;")
        self._lbl_indicador.setToolTip(f"Estado: {criticidad.capitalize()}")

        # Borde izquierdo de la tarjeta según criticidad
        self.setStyleSheet(
            f"QFrame#metric_card {{ border-left: 4px solid {color_hex}; border-radius: 14px; }}"
        )

        # Tendencia
        if tendencia == "sube":
            icono_tend = ICONOS["tendencia_sube"]
            color_tend = "#f59e0b"
            texto_tend = f"{icono_tend} +{tendencia_pct:.1f}%"
        elif tendencia == "baja":
            icono_tend = ICONOS["tendencia_baja"]
            color_tend = "#22c55e"
            texto_tend = f"{icono_tend} -{tendencia_pct:.1f}%"
        else:
            icono_tend = ICONOS["tendencia_estable"]
            color_tend = "#94a3b8"
            texto_tend = f"{icono_tend} Estable"

        self._lbl_tendencia.setText(texto_tend)
        self._lbl_tendencia.setStyleSheet(f"color: {color_tend}; font-size: 11px;")

        if subtexto:
            self._lbl_subtexto.setText(subtexto)

    def limpiar(self) -> None:
        """Muestra estado vacío cuando no hay datos para el día."""
        self.actualizar("—", CRITICIDAD_NORMAL, "estable", 0.0, "Sin datos hoy")
