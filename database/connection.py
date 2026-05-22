"""
Gestión de conexión a la base de datos SQLite.

Implementa el patrón Singleton para la sesión de SQLAlchemy,
garantizando una única conexión durante toda la ejecución.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import config
from models.base import Base

logger = logging.getLogger("healthtrack.database")


def _habilitar_fk(dbapi_conn, _connection_record) -> None:
    """Habilita claves foráneas en SQLite (desactivadas por defecto)."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")   # Mayor rendimiento concurrente
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


class GestorBaseDatos:
    """
    Singleton que administra el ciclo de vida de la base de datos.

    Uso:
        gestor = GestorBaseDatos()
        with gestor.sesion() as sesion:
            sesion.add(registro)
            sesion.commit()
    """

    _instancia: GestorBaseDatos | None = None
    _engine: Engine | None = None
    _SessionLocal: sessionmaker | None = None

    def __new__(cls) -> "GestorBaseDatos":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia

    def _inicializar(self) -> None:
        """Crea el engine, registra eventos y crea las tablas si no existen."""
        ruta_db = config.db_ruta
        ruta_db.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Inicializando base de datos en: %s", ruta_db)

        self._engine = create_engine(
            f"sqlite:///{ruta_db}",
            echo=config.debug,
            connect_args={"check_same_thread": False},
        )

        # Activar pragmas de rendimiento/seguridad en cada conexión
        event.listen(self._engine, "connect", _habilitar_fk)

        # Crear todas las tablas (idempotente)
        Base.metadata.create_all(self._engine)
        logger.info("Tablas de base de datos verificadas/creadas")

        self._SessionLocal = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> Engine:
        assert self._engine is not None
        return self._engine

    @contextmanager
    def sesion(self) -> Generator[Session, None, None]:
        """
        Context manager que provee una sesión con commit/rollback automático.

        Uso:
            with gestor.sesion() as s:
                s.add(obj)
        """
        assert self._SessionLocal is not None
        sesion = self._SessionLocal()
        try:
            yield sesion
            sesion.commit()
        except Exception as e:
            sesion.rollback()
            logger.error("Error en sesión de BD — rollback ejecutado: %s", e)
            raise
        finally:
            sesion.close()

    def verificar_conexion(self) -> bool:
        """Comprueba que la base de datos responde correctamente."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Verificación de conexión fallida: %s", e)
            return False

    def obtener_ruta(self) -> Path:
        """Devuelve la ruta física del archivo SQLite."""
        return config.db_ruta


# Instancia global
_gestor = GestorBaseDatos()


def obtener_sesion() -> Generator[Session, None, None]:
    """Helper shortcut para obtener una sesión de la instancia global."""
    return _gestor.sesion()


def obtener_gestor() -> GestorBaseDatos:
    """Devuelve la instancia singleton del gestor."""
    return _gestor
