"""
Gráfica de barras para comparativas y distribuciones en HealthTrack Pro.
"""

from __future__ import annotations

import logging
from typing import Optional

from charts.base_chart import GraficaBase
from core.constants import GRAFICA_COLORES_SERIES

logger = logging.getLogger("healthtrack.charts.barras")


class GraficaBarras(GraficaBase):
    """
    Gráfica de barras verticales u horizontales.

    Ideal para mostrar promedios semanales, comparativas
    de períodos y distribuciones de valores.
    """

    def __init__(
        self,
        titulo: str = "",
        unidad: str = "",
        horizontal: bool = False,
        alto_figura: float = 3.5,
        parent=None,
    ) -> None:
        self._categorias: list[str] = []
        self._valores: list[float] = []
        self._colores_barras: list[str] = []
        self._unidad = unidad
        self._horizontal = horizontal
        super().__init__(titulo=titulo, alto_figura=alto_figura, parent=parent)

    def cargar_datos(
        self,
        categorias: list[str],
        valores: list[float],
        colores: Optional[list[str]] = None,
    ) -> None:
        """Carga datos y redibuja."""
        self._categorias = categorias
        self._valores = valores
        self._colores_barras = colores or [
            GRAFICA_COLORES_SERIES[i % len(GRAFICA_COLORES_SERIES)]
            for i in range(len(valores))
        ]
        self.dibujar()

    def dibujar(self) -> None:
        self.limpiar()

        if not self._valores:
            self._ax.text(
                0.5, 0.5, "Sin datos disponibles",
                transform=self._ax.transAxes,
                ha="center", va="center",
                color=self.colores["texto_secundario"],
                fontsize=12,
            )
            self.refrescar()
            return

        colores = self.colores
        x = range(len(self._categorias))

        if self._horizontal:
            barras = self._ax.barh(
                self._categorias, self._valores,
                color=self._colores_barras, height=0.6,
                edgecolor="none",
            )
            self._ax.set_xlabel(self._unidad, color=colores["texto_secundario"], fontsize=9)
            # Etiquetas de valor al final de cada barra
            for barra, val in zip(barras, self._valores):
                self._ax.text(
                    barra.get_width() + (max(self._valores) * 0.01),
                    barra.get_y() + barra.get_height() / 2,
                    f"{val:.1f}",
                    va="center", ha="left",
                    color=colores["texto_secundario"], fontsize=8,
                )
        else:
            barras = self._ax.bar(
                x, self._valores,
                color=self._colores_barras,
                width=0.6, edgecolor="none",
            )
            self._ax.set_xticks(list(x))
            self._ax.set_xticklabels(
                self._categorias, rotation=20, ha="right",
                fontsize=9, color=colores["texto_secundario"],
            )
            if self._unidad:
                self._ax.set_ylabel(self._unidad, color=colores["texto_secundario"], fontsize=9)
            # Etiquetas sobre cada barra
            for barra, val in zip(barras, self._valores):
                self._ax.text(
                    barra.get_x() + barra.get_width() / 2,
                    barra.get_height() + (max(self._valores) * 0.015),
                    f"{val:.0f}" if val == int(val) else f"{val:.1f}",
                    ha="center", va="bottom",
                    color=colores["texto_secundario"], fontsize=8,
                )

        # Línea de promedio
        if len(self._valores) > 1:
            promedio = sum(self._valores) / len(self._valores)
            if self._horizontal:
                self._ax.axvline(
                    promedio, color="#6366f1", linewidth=1.2,
                    linestyle="--", alpha=0.7, label=f"Promedio: {promedio:.1f}",
                )
            else:
                self._ax.axhline(
                    promedio, color="#6366f1", linewidth=1.2,
                    linestyle="--", alpha=0.7, label=f"Promedio: {promedio:.1f}",
                )
            self._ax.legend(
                framealpha=0.0,
                labelcolor=colores["texto_secundario"],
                fontsize=9,
            )

        self.refrescar()
