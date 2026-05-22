"""
Clase base para todas las gráficas de HealthTrack Pro.

Gestiona la figura matplotlib embebida en PySide6, el tema visual,
el fondo transparente y los estilos comunes.
"""

from __future__ import annotations

import logging
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from core.constants import COLORES_OSCURO, COLORES_CLARO

matplotlib.use("QtAgg")
logger = logging.getLogger("healthtrack.charts")


class GraficaBase(QWidget):
    """
    Widget base para gráficas matplotlib integradas en Qt.

    Proporciona:
    - Canvas matplotlib auto-ajustable
    - Aplicación de tema (colores)
    - Métodos helper de estilo profesional
    - Método abstracto `dibujar()` que subclases deben implementar
    """

    def __init__(
        self,
        titulo: str = "",
        alto_figura: float = 3.5,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._titulo = titulo
        self._alto = alto_figura
        self._oscuro = True

        self._inicializar_figura()
        self._construir_layout()

    def _inicializar_figura(self) -> None:
        """Crea la figura y el canvas de matplotlib."""
        self._figura = Figure(figsize=(10, self._alto), dpi=96)
        self._figura.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.15)

        self._canvas = FigureCanvas(self._figura)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._ax = self._figura.add_subplot(111)
        self._aplicar_estilo_ejes()

    def _construir_layout(self) -> None:
        """Integra el canvas matplotlib en el widget Qt."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._canvas)

    def _aplicar_estilo_ejes(self) -> None:
        """Aplica el tema visual al área de la gráfica."""
        colores = COLORES_OSCURO if self._oscuro else COLORES_CLARO

        fondo_fig = colores["fondo_tarjeta"]
        fondo_ejes = colores["fondo_tarjeta"]
        color_texto = colores["texto_primario"]
        color_secundario = colores["texto_secundario"]
        color_grid = colores["grafica_grid"]

        self._figura.patch.set_facecolor(fondo_fig)
        self._ax.set_facecolor(fondo_ejes)

        # Grid sutil
        self._ax.yaxis.grid(True, color=color_grid, linewidth=0.6, linestyle="--", alpha=0.7)
        self._ax.xaxis.grid(False)
        self._ax.set_axisbelow(True)

        # Bordes del área
        for spine in self._ax.spines.values():
            spine.set_visible(False)

        # Ejes de referencia
        self._ax.spines["bottom"].set_visible(True)
        self._ax.spines["bottom"].set_color(color_grid)
        self._ax.spines["bottom"].set_linewidth(0.8)

        # Etiquetas de ejes
        self._ax.tick_params(
            axis="both",
            colors=color_secundario,
            labelsize=9,
            length=0,
        )

        # Título
        if self._titulo:
            self._ax.set_title(
                self._titulo,
                color=color_texto,
                fontsize=13,
                fontweight="bold",
                pad=12,
                loc="left",
            )

    def cambiar_tema(self, oscuro: bool) -> None:
        """Actualiza el tema y redibuja la gráfica."""
        self._oscuro = oscuro
        self._figura.clear()
        self._ax = self._figura.add_subplot(111)
        self._aplicar_estilo_ejes()
        self.dibujar()

    def limpiar(self) -> None:
        """Limpia el área de dibujo y aplica el estilo base."""
        self._ax.clear()
        self._aplicar_estilo_ejes()

    def refrescar(self) -> None:
        """Fuerza el redibujado del canvas."""
        self._canvas.draw_idle()

    def dibujar(self) -> None:
        """Método abstracto — subclases deben implementarlo."""
        raise NotImplementedError("Cada gráfica debe implementar dibujar()")

    @property
    def figura(self) -> Figure:
        return self._figura

    @property
    def ax(self):
        return self._ax

    @property
    def colores(self) -> dict[str, str]:
        return COLORES_OSCURO if self._oscuro else COLORES_CLARO
