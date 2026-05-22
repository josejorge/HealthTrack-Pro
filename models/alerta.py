"""
Modelo de alertas generadas automáticamente por el sistema.

Cada alerta está vinculada a un registro de salud y describe
un valor preocupante con su nivel de criticidad.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Alerta(Base):
    """Alerta de salud generada por el motor de reglas."""

    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Vinculación al registro
    registro_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Datos de la alerta
    metrica: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    criticidad: Mapped[str] = mapped_column(String(20), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recomendacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Estado
    vista: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resuelta: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Auditoría
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"Alerta(id={self.id}, metrica={self.metrica!r}, "
            f"criticidad={self.criticidad!r}, fecha={self.fecha})"
        )
