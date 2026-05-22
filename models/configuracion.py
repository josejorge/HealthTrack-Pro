"""
Modelo de configuración persistida en base de datos.

Almacena preferencias del usuario como pares clave-valor,
complementando el archivo JSON de configuración.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ConfiguracionUsuario(Base):
    """Tabla de configuración clave-valor del usuario."""

    __tablename__ = "configuracion_usuario"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=True)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"ConfiguracionUsuario(clave={self.clave!r}, valor={self.valor!r})"
