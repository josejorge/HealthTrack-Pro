"""
Servicio de estadísticas y análisis de datos de salud.

Calcula promedios, medianas, tendencias, desviación estándar,
récords históricos y correlaciones entre métricas.
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from database.connection import obtener_gestor
from database.repositories.registro_repository import RepositorioRegistro

logger = logging.getLogger("healthtrack.services.estadisticas")


@dataclass
class ResumenEstadistico:
    """Resumen estadístico completo de una métrica."""

    metrica: str
    etiqueta: str
    unidad: str
    promedio: Optional[float] = None
    mediana: Optional[float] = None
    minimo: Optional[float] = None
    maximo: Optional[float] = None
    desviacion_std: Optional[float] = None
    total_registros: int = 0
    tendencia: str = "estable"      # "sube" | "baja" | "estable"
    tendencia_porcentaje: float = 0.0
    fecha_maximo: Optional[date] = None
    fecha_minimo: Optional[date] = None
    valores_recientes: list[float] = field(default_factory=list)
    fechas_recientes: list[date] = field(default_factory=list)


@dataclass
class RecordHistorico:
    """Récord personal (máximo o mínimo histórico) de una métrica."""

    metrica: str
    etiqueta: str
    unidad: str
    valor: float
    fecha: date
    periodo: str
    tipo: str  # "maximo" | "minimo"


class ServicioEstadisticas:
    """
    Servicio de estadísticas avanzadas para métricas de salud.

    Todos los cálculos trabajan sobre datos reales de la base de datos,
    sin redondeo artificioso ni valores simulados.
    """

    # Mapa de métricas con su etiqueta amigable y unidad de medida
    METRICAS_INFO: dict[str, tuple[str, str]] = {
        "presion_sistolica": ("Presión sistólica", "mmHg"),
        "presion_diastolica": ("Presión diastólica", "mmHg"),
        "ritmo_cardiaco": ("Ritmo cardíaco", "bpm"),
        "oxigenacion": ("Oxigenación SpO2", "%"),
        "peso": ("Peso", "kg"),
        "imc": ("IMC", "kg/m²"),
        "pasos": ("Pasos", "pasos"),
        "distancia_caminada": ("Distancia caminada", "km"),
        "calorias_quemadas": ("Calorías quemadas", "kcal"),
        "horas_sueno": ("Horas de sueño", "h"),
        "calidad_sueno": ("Calidad del sueño", "/10"),
        "nivel_estres": ("Nivel de estrés", "/10"),
        "estado_animo": ("Estado de ánimo", "/10"),
        "glucosa": ("Glucosa", "mg/dL"),
        "temperatura_corporal": ("Temperatura", "°C"),
        "consumo_agua": ("Consumo de agua", "L"),
        "cafeina": ("Cafeína", "mg"),
    }

    def __init__(self) -> None:
        self._gestor = obtener_gestor()

    # ──────────────────────────────────────────
    # Resumen estadístico completo
    # ──────────────────────────────────────────

    def calcular_resumen(
        self,
        metrica: str,
        dias: int = 30,
    ) -> Optional[ResumenEstadistico]:
        """
        Calcula un resumen estadístico completo para una métrica.

        Args:
            metrica: Nombre del campo en RegistroSalud.
            dias: Cuántos días hacia atrás incluir.

        Returns:
            ResumenEstadistico con todos los valores calculados.
        """
        if metrica not in self.METRICAS_INFO:
            logger.warning("Métrica desconocida: %s", metrica)
            return None

        etiqueta, unidad = self.METRICAS_INFO[metrica]

        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)
            fecha_inicio = date.today() - timedelta(days=dias)
            filas = repo.valores_metrica(metrica, fecha_inicio, date.today())

        if not filas:
            return ResumenEstadistico(metrica=metrica, etiqueta=etiqueta, unidad=unidad)

        valores = [float(v) for _, _, v in filas if v is not None]
        fechas = [f for f, _, v in filas if v is not None]

        if not valores:
            return ResumenEstadistico(metrica=metrica, etiqueta=etiqueta, unidad=unidad)

        resumen = ResumenEstadistico(
            metrica=metrica,
            etiqueta=etiqueta,
            unidad=unidad,
            promedio=round(statistics.mean(valores), 2),
            mediana=round(statistics.median(valores), 2),
            minimo=min(valores),
            maximo=max(valores),
            desviacion_std=round(statistics.stdev(valores), 2) if len(valores) > 1 else 0.0,
            total_registros=len(valores),
            valores_recientes=valores[-14:],
            fechas_recientes=fechas[-14:],
        )

        # Fechas de récords
        idx_max = valores.index(max(valores))
        idx_min = valores.index(min(valores))
        resumen.fecha_maximo = fechas[idx_max]
        resumen.fecha_minimo = fechas[idx_min]

        # Tendencia: compara primera mitad vs segunda mitad del período
        resumen.tendencia, resumen.tendencia_porcentaje = self._calcular_tendencia(valores)

        return resumen

    # ──────────────────────────────────────────
    # Récords históricos
    # ──────────────────────────────────────────

    def obtener_records_historicos(self) -> list[RecordHistorico]:
        """
        Devuelve los récords máximos y mínimos históricos para las métricas principales.
        """
        records: list[RecordHistorico] = []
        metricas_principales = [
            "presion_sistolica", "presion_diastolica", "ritmo_cardiaco",
            "oxigenacion", "peso", "pasos", "glucosa",
        ]

        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)

            for metrica in metricas_principales:
                etiqueta, unidad = self.METRICAS_INFO.get(metrica, (metrica, ""))

                reg_max = repo.maximo_metrica(metrica)
                if reg_max:
                    valor = getattr(reg_max, metrica)
                    if valor is not None:
                        records.append(RecordHistorico(
                            metrica=metrica,
                            etiqueta=etiqueta,
                            unidad=unidad,
                            valor=float(valor),
                            fecha=reg_max.fecha,
                            periodo=reg_max.periodo,
                            tipo="maximo",
                        ))

                reg_min = repo.minimo_metrica(metrica)
                if reg_min:
                    valor = getattr(reg_min, metrica)
                    if valor is not None:
                        records.append(RecordHistorico(
                            metrica=metrica,
                            etiqueta=etiqueta,
                            unidad=unidad,
                            valor=float(valor),
                            fecha=reg_min.fecha,
                            periodo=reg_min.periodo,
                            tipo="minimo",
                        ))

        return records

    # ──────────────────────────────────────────
    # Series temporales (para gráficas)
    # ──────────────────────────────────────────

    def serie_temporal(
        self,
        metrica: str,
        dias: int = 30,
    ) -> tuple[list[date], list[float]]:
        """
        Devuelve (fechas, valores) para graficar una métrica en el tiempo.

        Cuando hay múltiples registros en el mismo día, devuelve el promedio diario.
        """
        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)
            fecha_inicio = date.today() - timedelta(days=dias)
            filas = repo.valores_metrica(metrica, fecha_inicio, date.today())

        # Agrupar por fecha (promedio del día)
        agrupado: dict[date, list[float]] = {}
        for fecha, _periodo, valor in filas:
            if valor is not None:
                agrupado.setdefault(fecha, []).append(float(valor))

        fechas_ordenadas = sorted(agrupado.keys())
        valores_promedio = [
            round(statistics.mean(agrupado[f]), 2) for f in fechas_ordenadas
        ]

        return fechas_ordenadas, valores_promedio

    def series_multiples(
        self,
        metricas: list[str],
        dias: int = 30,
    ) -> dict[str, tuple[list[date], list[float]]]:
        """Devuelve series temporales para múltiples métricas simultáneamente."""
        return {m: self.serie_temporal(m, dias) for m in metricas}

    # ──────────────────────────────────────────
    # Comparativas de períodos
    # ──────────────────────────────────────────

    def comparar_periodos(
        self,
        metrica: str,
        dias_periodo1: int = 30,
        dias_periodo2: int = 60,
    ) -> dict[str, Optional[float]]:
        """
        Compara el promedio de una métrica entre dos períodos.

        Returns:
            Diccionario con promedios y variación porcentual.
        """
        hoy = date.today()

        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)

            prom_reciente = repo.promedio_metrica(
                metrica,
                hoy - timedelta(days=dias_periodo1),
                hoy,
            )
            prom_anterior = repo.promedio_metrica(
                metrica,
                hoy - timedelta(days=dias_periodo2),
                hoy - timedelta(days=dias_periodo1),
            )

        variacion = None
        if prom_reciente is not None and prom_anterior and prom_anterior != 0:
            variacion = round(((prom_reciente - prom_anterior) / prom_anterior) * 100, 1)

        return {
            "promedio_reciente": prom_reciente,
            "promedio_anterior": prom_anterior,
            "variacion_porcentaje": variacion,
        }

    # ──────────────────────────────────────────
    # Resumen del día actual
    # ──────────────────────────────────────────

    def resumen_hoy(self) -> dict[str, Any]:
        """
        Genera un resumen rápido del día actual con las métricas disponibles.
        """
        from services.registro_service import ServicioRegistro
        servicio = ServicioRegistro()
        registros_hoy = servicio.obtener_hoy()

        if not registros_hoy:
            return {"tiene_datos": False, "registros": 0}

        # Promediar métricas del día
        resumen: dict[str, Any] = {"tiene_datos": True, "registros": len(registros_hoy)}

        metricas_num = [
            "presion_sistolica", "presion_diastolica", "ritmo_cardiaco",
            "oxigenacion", "peso", "pasos", "horas_sueno", "nivel_estres",
            "estado_animo", "glucosa", "temperatura_corporal", "consumo_agua",
        ]

        for metrica in metricas_num:
            valores = [
                getattr(r, metrica)
                for r in registros_hoy
                if getattr(r, metrica) is not None
            ]
            if valores:
                resumen[metrica] = round(statistics.mean(valores), 2)

        # Criticidad general del día
        criticidades = [r.criticidad_general() for r in registros_hoy]
        orden = ["critico", "preocupante", "atencion", "normal"]
        for nivel in orden:
            if nivel in criticidades:
                resumen["criticidad_general"] = nivel
                break
        else:
            resumen["criticidad_general"] = "normal"

        return resumen

    # ──────────────────────────────────────────
    # Helpers internos
    # ──────────────────────────────────────────

    @staticmethod
    def _calcular_tendencia(valores: list[float]) -> tuple[str, float]:
        """
        Determina la tendencia comparando la primera vs segunda mitad de la serie.

        Returns:
            Tupla (dirección, porcentaje_cambio).
        """
        if len(valores) < 4:
            return "estable", 0.0

        mitad = len(valores) // 2
        primera_mitad = statistics.mean(valores[:mitad])
        segunda_mitad = statistics.mean(valores[mitad:])

        if primera_mitad == 0:
            return "estable", 0.0

        cambio = ((segunda_mitad - primera_mitad) / abs(primera_mitad)) * 100

        if cambio > 3:
            return "sube", round(cambio, 1)
        elif cambio < -3:
            return "baja", round(abs(cambio), 1)
        else:
            return "estable", round(abs(cambio), 1)


# Importación tardía para evitar circular import
from typing import Any
