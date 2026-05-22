"""
Repositorio base genérico con operaciones CRUD comunes.

Todos los repositorios concretos heredan de esta clase
para compartir la implementación estándar de acceso a datos.
"""

from __future__ import annotations

import logging
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from models.base import Base

T = TypeVar("T", bound=Base)
logger = logging.getLogger("healthtrack.repository")


class RepositorioBase(Generic[T]):
    """Repositorio base con operaciones CRUD genéricas."""

    def __init__(self, modelo: Type[T], sesion: Session) -> None:
        self.modelo = modelo
        self.sesion = sesion

    def obtener_por_id(self, id_registro: int) -> Optional[T]:
        """Obtiene un registro por su clave primaria."""
        return self.sesion.get(self.modelo, id_registro)

    def obtener_todos(self) -> list[T]:
        """Obtiene todos los registros de la tabla."""
        return self.sesion.query(self.modelo).all()

    def guardar(self, entidad: T) -> T:
        """Persiste una entidad nueva o actualizada."""
        self.sesion.add(entidad)
        self.sesion.flush()
        return entidad

    def eliminar(self, entidad: T) -> None:
        """Elimina una entidad de la base de datos."""
        self.sesion.delete(entidad)
        self.sesion.flush()

    def eliminar_por_id(self, id_registro: int) -> bool:
        """Elimina una entidad por ID. Devuelve True si fue encontrada y eliminada."""
        entidad = self.obtener_por_id(id_registro)
        if entidad is None:
            return False
        self.eliminar(entidad)
        return True

    def contar(self) -> int:
        """Cuenta el total de registros en la tabla."""
        return self.sesion.query(self.modelo).count()
