"""
Servicio de insights automáticos.

Analiza patrones en los datos del usuario y genera textos
explicativos en lenguaje natural sobre su salud.
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from database.connection import obtener_gestor
from database.repositories.registro_repository import RepositorioRegistro

logger = logging.getLogger("healthtrack.services.insights")


@dataclass
class Insight:
    """Un insight individual generado automáticamente."""

    icono: str
    texto: str
    categoria: str      # "cardiovascular" | "fisica" | "sueno" | "mental" | "general"
    positivo: bool      # True = buena noticia, False = alerta/sugerencia


class ServicioInsights:
    """
    Genera observaciones automáticas sobre las tendencias de salud del usuario.

    Los insights se basan en comparaciones reales de datos, no en textos fijos.
    """

    def __init__(self) -> None:
        self._gestor = obtener_gestor()

    def generar_insights(self, dias: int = 30) -> list[Insight]:
        """
        Genera hasta 8 insights basados en los últimos N días de datos.

        Args:
            dias: Número de días a analizar.

        Returns:
            Lista de Insight ordenada por relevancia.
        """
        insights: list[Insight] = []

        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)
            fecha_inicio = date.today() - timedelta(days=dias)
            registros = repo.obtener_rango(fecha_inicio, date.today())

        if len(registros) < 3:
            insights.append(Insight(
                icono="📊",
                texto="Registra más datos para obtener insights personalizados.",
                categoria="general",
                positivo=True,
            ))
            return insights

        # Analizar cada dimensión
        insights.extend(self._analizar_presion(registros))
        insights.extend(self._analizar_sueno(registros))
        insights.extend(self._analizar_actividad(registros))
        insights.extend(self._analizar_estres_presion(registros))
        insights.extend(self._analizar_tendencia_peso(registros))
        insights.extend(self._analizar_consistencia(registros, dias))

        # Limitar a 8 insights más relevantes
        return insights[:8]

    # ──────────────────────────────────────────
    # Analizadores por dimensión
    # ──────────────────────────────────────────

    def _analizar_presion(self, registros) -> list[Insight]:
        """Detecta tendencias en la presión arterial."""
        insights = []
        sistolicas = [r.presion_sistolica for r in registros if r.presion_sistolica]
        if len(sistolicas) < 4:
            return insights

        mitad = len(sistolicas) // 2
        prom_reciente = statistics.mean(sistolicas[mitad:])
        prom_anterior = statistics.mean(sistolicas[:mitad])

        if prom_anterior > 0:
            cambio = ((prom_reciente - prom_anterior) / prom_anterior) * 100
            if cambio >= 5:
                insights.append(Insight(
                    icono="❤️",
                    texto=f"Tu presión arterial ha aumentado un {cambio:.1f}% en este período.",
                    categoria="cardiovascular",
                    positivo=False,
                ))
            elif cambio <= -5:
                insights.append(Insight(
                    icono="❤️",
                    texto=f"Tu presión arterial ha mejorado un {abs(cambio):.1f}% en este período. ¡Excelente!",
                    categoria="cardiovascular",
                    positivo=True,
                ))

        return insights

    def _analizar_sueno(self, registros) -> list[Insight]:
        """Detecta patrones y tendencias en el sueño."""
        insights = []
        sueno = [r.horas_sueno for r in registros if r.horas_sueno]
        if not sueno:
            return insights

        promedio = statistics.mean(sueno)

        if len(sueno) >= 6:
            mitad = len(sueno) // 2
            prom_reciente = statistics.mean(sueno[mitad:])
            prom_anterior = statistics.mean(sueno[:mitad])
            if prom_anterior > 0:
                cambio = ((prom_reciente - prom_anterior) / prom_anterior) * 100
                if cambio >= 10:
                    insights.append(Insight(
                        icono="😴",
                        texto=f"Tu sueño ha mejorado un {cambio:.1f}% en las últimas semanas.",
                        categoria="sueno",
                        positivo=True,
                    ))
                elif cambio <= -10:
                    insights.append(Insight(
                        icono="😴",
                        texto=f"Tu sueño ha disminuido un {abs(cambio):.1f}% recientemente. Prioriza el descanso.",
                        categoria="sueno",
                        positivo=False,
                    ))

        if promedio < 7:
            insights.append(Insight(
                icono="🌙",
                texto=f"Promedio de {promedio:.1f}h de sueño — por debajo del objetivo de 7–9h.",
                categoria="sueno",
                positivo=False,
            ))
        elif promedio >= 7:
            insights.append(Insight(
                icono="🌙",
                texto=f"Buen promedio de sueño: {promedio:.1f}h por noche.",
                categoria="sueno",
                positivo=True,
            ))

        return insights

    def _analizar_actividad(self, registros) -> list[Insight]:
        """Analiza la actividad física del usuario."""
        insights = []
        pasos = [r.pasos for r in registros if r.pasos]
        if not pasos:
            return insights

        promedio = statistics.mean(pasos)
        objetivo = 10000

        porcentaje = (promedio / objetivo) * 100

        if porcentaje >= 100:
            insights.append(Insight(
                icono="🏃",
                texto=f"¡Estás cumpliendo tu objetivo de pasos! Promedio: {promedio:,.0f} pasos/día.",
                categoria="fisica",
                positivo=True,
            ))
        elif porcentaje >= 70:
            insights.append(Insight(
                icono="👟",
                texto=f"Promedio de {promedio:,.0f} pasos/día — a un {100-porcentaje:.0f}% de tu objetivo.",
                categoria="fisica",
                positivo=True,
            ))
        else:
            insights.append(Insight(
                icono="🦶",
                texto=f"Solo {promedio:,.0f} pasos diarios en promedio. Intenta caminar más.",
                categoria="fisica",
                positivo=False,
            ))

        return insights

    def _analizar_estres_presion(self, registros) -> list[Insight]:
        """Detecta correlación entre estrés y presión arterial."""
        insights = []
        pares = [
            (r.nivel_estres, r.presion_sistolica)
            for r in registros
            if r.nivel_estres and r.presion_sistolica
        ]

        if len(pares) < 6:
            return insights

        # Días de estrés alto vs bajo
        alto_estres = [p for p in pares if p[0] >= 7]
        bajo_estres = [p for p in pares if p[0] <= 4]

        if alto_estres and bajo_estres:
            prom_presion_alta = statistics.mean(p[1] for p in alto_estres)
            prom_presion_baja = statistics.mean(p[1] for p in bajo_estres)
            diferencia = prom_presion_alta - prom_presion_baja

            if diferencia >= 8:
                insights.append(Insight(
                    icono="🧠",
                    texto=(
                        f"Cuando tu estrés es alto, tu presión arterial es "
                        f"{diferencia:.0f} mmHg mayor en promedio."
                    ),
                    categoria="mental",
                    positivo=False,
                ))

        return insights

    def _analizar_tendencia_peso(self, registros) -> list[Insight]:
        """Detecta cambios significativos en el peso."""
        insights = []
        pesos = [(r.fecha, r.peso) for r in registros if r.peso]
        if len(pesos) < 4:
            return insights

        peso_inicial = pesos[0][1]
        peso_final = pesos[-1][1]
        cambio = peso_final - peso_inicial

        if abs(cambio) >= 2:
            if cambio < 0:
                insights.append(Insight(
                    icono="⚖️",
                    texto=f"Has bajado {abs(cambio):.1f} kg en este período. ¡Buen progreso!",
                    categoria="fisica",
                    positivo=True,
                ))
            else:
                insights.append(Insight(
                    icono="⚖️",
                    texto=f"Tu peso ha aumentado {cambio:.1f} kg en este período.",
                    categoria="fisica",
                    positivo=False,
                ))

        return insights

    def _analizar_consistencia(self, registros, dias: int) -> list[Insight]:
        """Evalúa la constancia en el registro de datos."""
        insights = []
        fechas_unicas = len({r.fecha for r in registros})
        porcentaje_cobertura = (fechas_unicas / dias) * 100

        if porcentaje_cobertura >= 80:
            insights.append(Insight(
                icono="🏆",
                texto=f"Excelente constancia: datos registrados en {fechas_unicas} de {dias} días.",
                categoria="general",
                positivo=True,
            ))
        elif porcentaje_cobertura < 40:
            insights.append(Insight(
                icono="📝",
                texto=f"Solo {fechas_unicas} días registrados de {dias}. Registra más para mejores insights.",
                categoria="general",
                positivo=False,
            ))

        return insights
