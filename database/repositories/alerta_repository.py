"""
Repositorio de alertas de salud.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from database.repositories.base_repository import RepositorioBase
from models.alerta import Alerta

logger = logging.getLogger("healthtrack.repository.alerta")


class RepositorioAlerta(RepositorioBase[Alerta]):
    """Repositorio para operaciones sobre Alerta."""

    def __init__(self, sesion: Session) -> None:
        super().__init__(Alerta, sesion)

    def obtener_no_vistas(self) -> list[Alerta]:
        """Devuelve alertas que el usuario aún no ha visto."""
        return (
            self.sesion.query(Alerta)
            .filter(Alerta.vista == False, Alerta.resuelta == False)
            .order_by(Alerta.fecha_creacion.desc())
            .all()
        )

    def obtener_activas(self) -> list[Alerta]:
        """Devuelve alertas no resueltas."""
        return (
            self.sesion.query(Alerta)
            .filter(Alerta.resuelta == False)
            .order_by(Alerta.fecha_creacion.desc())
            .limit(50)
            .all()
        )

    def obtener_por_fecha(self, fecha: date) -> list[Alerta]:
        """Devuelve alertas de una fecha específica."""
        return (
            self.sesion.query(Alerta)
            .filter(Alerta.fecha == fecha)
            .order_by(Alerta.fecha_creacion.desc())
            .all()
        )

    def marcar_todas_vistas(self) -> int:
        """Marca todas las alertas pendientes como vistas. Devuelve el número actualizado."""
        actualizadas = (
            self.sesion.query(Alerta)
            .filter(Alerta.vista == False)
            .update({"vista": True})
        )
        self.sesion.flush()
        return actualizadas

    def contar_no_vistas(self) -> int:
        """Cuenta las alertas pendientes de revisar."""
        return (
            self.sesion.query(Alerta)
            .filter(Alerta.vista == False, Alerta.resuelta == False)
            .count()
        )

    def existe_alerta_para_registro(self, registro_id: int, metrica: str) -> bool:
        """Verifica si ya existe una alerta para el registro y métrica dados."""
        return (
            self.sesion.query(Alerta)
            .filter(Alerta.registro_id == registro_id, Alerta.metrica == metrica)
            .count()
            > 0
        )
