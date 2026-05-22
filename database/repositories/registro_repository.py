"""
Repositorio de registros de salud.

Encapsula toda la lógica de consulta a la tabla registros_salud,
exponiendo métodos de dominio semánticos en lugar de SQL crudo.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from database.repositories.base_repository import RepositorioBase
from models.registro_salud import RegistroSalud

logger = logging.getLogger("healthtrack.repository.registro")


class RepositorioRegistro(RepositorioBase[RegistroSalud]):
    """Repositorio para operaciones sobre RegistroSalud."""

    def __init__(self, sesion: Session) -> None:
        super().__init__(RegistroSalud, sesion)

    # ──────────────────────────────────────────
    # Consultas por fecha y período
    # ──────────────────────────────────────────

    def obtener_por_fecha_y_periodo(
        self, fecha: date, periodo: str
    ) -> Optional[RegistroSalud]:
        """Devuelve el registro de una fecha y período específicos."""
        return (
            self.sesion.query(RegistroSalud)
            .filter(
                RegistroSalud.fecha == fecha,
                RegistroSalud.periodo == periodo,
            )
            .first()
        )

    def obtener_por_fecha(self, fecha: date) -> list[RegistroSalud]:
        """Devuelve todos los registros de un día."""
        return (
            self.sesion.query(RegistroSalud)
            .filter(RegistroSalud.fecha == fecha)
            .order_by(RegistroSalud.periodo)
            .all()
        )

    def obtener_rango(
        self, fecha_inicio: date, fecha_fin: date
    ) -> list[RegistroSalud]:
        """Devuelve registros en un rango de fechas (inclusivo)."""
        return (
            self.sesion.query(RegistroSalud)
            .filter(
                RegistroSalud.fecha >= fecha_inicio,
                RegistroSalud.fecha <= fecha_fin,
            )
            .order_by(RegistroSalud.fecha, RegistroSalud.periodo)
            .all()
        )

    def obtener_ultimos_dias(self, dias: int) -> list[RegistroSalud]:
        """Devuelve los registros de los últimos N días."""
        fecha_inicio = date.today() - timedelta(days=dias)
        return self.obtener_rango(fecha_inicio, date.today())

    def obtener_recientes(self, limite: int = 10) -> list[RegistroSalud]:
        """Devuelve los N registros más recientes."""
        return (
            self.sesion.query(RegistroSalud)
            .order_by(RegistroSalud.fecha.desc(), RegistroSalud.id.desc())
            .limit(limite)
            .all()
        )

    def obtener_ultimo(self) -> Optional[RegistroSalud]:
        """Devuelve el registro más reciente."""
        return (
            self.sesion.query(RegistroSalud)
            .order_by(RegistroSalud.fecha.desc(), RegistroSalud.id.desc())
            .first()
        )

    # ──────────────────────────────────────────
    # Estadísticas sobre métricas numéricas
    # ──────────────────────────────────────────

    def maximo_metrica(self, metrica: str) -> Optional[RegistroSalud]:
        """Devuelve el registro con el valor máximo de la métrica indicada."""
        col = getattr(RegistroSalud, metrica, None)
        if col is None:
            return None
        return (
            self.sesion.query(RegistroSalud)
            .filter(col.isnot(None))
            .order_by(col.desc())
            .first()
        )

    def minimo_metrica(self, metrica: str) -> Optional[RegistroSalud]:
        """Devuelve el registro con el valor mínimo de la métrica indicada."""
        col = getattr(RegistroSalud, metrica, None)
        if col is None:
            return None
        return (
            self.sesion.query(RegistroSalud)
            .filter(col.isnot(None))
            .order_by(col.asc())
            .first()
        )

    def promedio_metrica(
        self,
        metrica: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> Optional[float]:
        """Calcula el promedio de una métrica en un período dado."""
        col = getattr(RegistroSalud, metrica, None)
        if col is None:
            return None
        query = self.sesion.query(func.avg(col)).filter(col.isnot(None))
        if fecha_inicio:
            query = query.filter(RegistroSalud.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(RegistroSalud.fecha <= fecha_fin)
        resultado = query.scalar()
        return round(float(resultado), 2) if resultado is not None else None

    def valores_metrica(
        self,
        metrica: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> list[tuple[date, str, float]]:
        """
        Devuelve lista de (fecha, periodo, valor) para una métrica.

        Útil para construir series temporales en gráficas.
        """
        col = getattr(RegistroSalud, metrica, None)
        if col is None:
            return []
        query = (
            self.sesion.query(RegistroSalud.fecha, RegistroSalud.periodo, col)
            .filter(col.isnot(None))
        )
        if fecha_inicio:
            query = query.filter(RegistroSalud.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(RegistroSalud.fecha <= fecha_fin)
        return query.order_by(RegistroSalud.fecha, RegistroSalud.periodo).all()

    # ──────────────────────────────────────────
    # Existencia y conteo
    # ──────────────────────────────────────────

    def existe_para_fecha_y_periodo(self, fecha: date, periodo: str) -> bool:
        """Verifica si ya existe un registro para la fecha y período dados."""
        return (
            self.sesion.query(RegistroSalud)
            .filter(
                RegistroSalud.fecha == fecha,
                RegistroSalud.periodo == periodo,
            )
            .count()
            > 0
        )

    def fechas_con_registros(
        self, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None
    ) -> list[date]:
        """Devuelve lista de fechas únicas que tienen al menos un registro."""
        query = self.sesion.query(RegistroSalud.fecha).distinct()
        if fecha_inicio:
            query = query.filter(RegistroSalud.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(RegistroSalud.fecha <= fecha_fin)
        return [row[0] for row in query.order_by(RegistroSalud.fecha).all()]

    def contar_por_periodo(self) -> dict[str, int]:
        """Cuenta registros agrupados por período del día."""
        resultado = (
            self.sesion.query(RegistroSalud.periodo, func.count(RegistroSalud.id))
            .group_by(RegistroSalud.periodo)
            .all()
        )
        return {periodo: count for periodo, count in resultado}
