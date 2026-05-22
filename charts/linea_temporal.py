"""
Gráfica de línea temporal para series de métricas de salud.

Soporta múltiples series, anotaciones de máximo/mínimo,
área rellena bajo la curva y zonas de referencia clínica.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.lines import Line2D

from charts.base_chart import GraficaBase
from core.constants import GRAFICA_COLORES_SERIES

logger = logging.getLogger("healthtrack.charts.linea")


class GraficaLineaTemporal(GraficaBase):
    """
    Gráfica de línea(s) temporal(es) con soporte para:
    - Múltiples series en el mismo eje
    - Área rellena bajo la curva
    - Anotación del máximo y mínimo
    - Zonas de referencia clínica (verde/rojo)
    - Promedio móvil opcional
    """

    def __init__(
        self,
        titulo: str = "",
        unidad: str = "",
        alto_figura: float = 3.5,
        parent=None,
    ) -> None:
        self._series: list[tuple[list[date], list[float], str, str]] = []
        self._unidad = unidad
        self._zona_normal: Optional[tuple[float, float]] = None
        self._zona_peligro: Optional[tuple[float, float]] = None
        super().__init__(titulo=titulo, alto_figura=alto_figura, parent=parent)

    def agregar_serie(
        self,
        fechas: list[date],
        valores: list[float],
        etiqueta: str = "",
        color: Optional[str] = None,
    ) -> None:
        """Agrega una serie de datos a la gráfica."""
        color = color or GRAFICA_COLORES_SERIES[len(self._series) % len(GRAFICA_COLORES_SERIES)]
        self._series.append((fechas, valores, etiqueta, color))

    def establecer_zona_normal(self, minimo: float, maximo: float) -> None:
        """Define la franja verde de valores normales."""
        self._zona_normal = (minimo, maximo)

    def establecer_zona_peligro(self, umbral: float) -> None:
        """Define el umbral a partir del cual el área se marca en rojo."""
        self._zona_peligro = (umbral, umbral + 999)

    def limpiar_series(self) -> None:
        """Elimina todas las series para redibujar con nuevos datos."""
        self._series.clear()
        self.limpiar()

    def dibujar(self) -> None:
        """Renderiza todas las series en el canvas."""
        self.limpiar()

        if not self._series:
            self._ax.text(
                0.5, 0.5, "Sin datos para el período seleccionado",
                transform=self._ax.transAxes,
                ha="center", va="center",
                color=self.colores["texto_secundario"],
                fontsize=12,
            )
            self.refrescar()
            return

        colores = self.colores

        # ── Zonas de referencia ───────────────────
        if self._zona_normal:
            self._ax.axhspan(
                self._zona_normal[0], self._zona_normal[1],
                alpha=0.06, color="#22c55e", label="_nolegend_",
            )
        if self._zona_peligro:
            # Solo dibujar si el umbral es alcanzable
            self._ax.axhline(
                self._zona_peligro[0],
                color="#ef4444", linewidth=1.0, linestyle="--", alpha=0.5,
                label=f"Umbral crítico",
            )

        # ── Series ───────────────────────────────
        for fechas, valores, etiqueta, color in self._series:
            if not fechas or not valores:
                continue

            import matplotlib.dates as mdates

            # Convertir fechas a formato matplotlib
            fechas_mpl = mdates.date2num(fechas)

            # Línea principal
            self._ax.plot(
                fechas_mpl, valores,
                color=color,
                linewidth=2.2,
                marker="o",
                markersize=4,
                markerfacecolor="white",
                markeredgecolor=color,
                markeredgewidth=1.5,
                label=etiqueta,
                solid_capstyle="round",
                solid_joinstyle="round",
            )

            # Área rellena bajo la curva (sutil)
            self._ax.fill_between(
                fechas_mpl, valores,
                alpha=0.08, color=color,
            )

            # Promedio móvil (si hay suficientes puntos)
            if len(valores) >= 5:
                ventana = min(5, len(valores))
                promedio_movil = np.convolve(
                    valores, np.ones(ventana) / ventana, mode="valid"
                )
                fechas_ma = fechas_mpl[ventana - 1:]
                self._ax.plot(
                    fechas_ma, promedio_movil,
                    color=color, linewidth=1.2, linestyle="--",
                    alpha=0.6, label=f"Media móvil ({ventana}d)",
                )

            # Anotación del máximo
            if len(valores) > 1:
                idx_max = valores.index(max(valores))
                self._ax.annotate(
                    f"▲ {max(valores):.1f}",
                    xy=(fechas_mpl[idx_max], max(valores)),
                    xytext=(0, 10),
                    textcoords="offset points",
                    color=color,
                    fontsize=8,
                    fontweight="bold",
                    ha="center",
                )

        # ── Formato del eje X ─────────────────────
        self._ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        self._ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self._figura.autofmt_xdate(rotation=30, ha="right")

        # ── Unidad en eje Y ───────────────────────
        if self._unidad:
            self._ax.set_ylabel(self._unidad, color=colores["texto_secundario"], fontsize=9)

        # ── Leyenda ───────────────────────────────
        etiquetas = [s[2] for s in self._series if s[2]]
        if etiquetas or self._zona_peligro:
            leyenda = self._ax.legend(
                loc="upper left",
                framealpha=0.0,
                labelcolor=colores["texto_secundario"],
                fontsize=9,
            )

        self.refrescar()


class GraficaPresionArterial(GraficaLineaTemporal):
    """
    Gráfica especializada para presión arterial.

    Muestra sistólica y diastólica en la misma gráfica
    con zonas de referencia clínicas según guías AHA.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(
            titulo="Presión Arterial",
            unidad="mmHg",
            alto_figura=3.5,
            parent=parent,
        )
        self.establecer_zona_normal(60, 120)
        self.establecer_zona_peligro(140)

    def cargar_datos(
        self,
        fechas_sistolica: list[date],
        valores_sistolica: list[float],
        fechas_diastolica: list[date],
        valores_diastolica: list[float],
    ) -> None:
        """Carga ambas series de presión y redibuja."""
        self.limpiar_series()
        self.agregar_serie(fechas_sistolica, valores_sistolica, "Sistólica", "#ef4444")
        self.agregar_serie(fechas_diastolica, valores_diastolica, "Diastólica", "#6366f1")
        self.dibujar()
