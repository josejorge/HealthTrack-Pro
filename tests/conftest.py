"""
Configuración de pytest para HealthTrack Pro.

Usa una base de datos SQLite en memoria para tests aislados.
"""

import sys
import os
from datetime import date

import pytest

# Ajustar path para importar módulos del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


@pytest.fixture(scope="function")
def db_temporal(tmp_path, monkeypatch):
    """
    Fixture que provee una base de datos SQLite temporal por test.

    Sobrescribe la ruta de la BD en la configuración para usar un archivo
    temporal que se limpia automáticamente al finalizar cada test.
    """
    ruta_temp = tmp_path / "test_healthtrack.db"

    # Sobrescribir la ruta de la BD en la configuración
    monkeypatch.setattr("core.config.RUTA_CONFIG", tmp_path / "settings.json")

    # Resetear el singleton de la BD para usar la temporal
    import database.connection as conn_mod
    conn_mod._gestor = None  # type: ignore

    # Parchar la ruta de la BD
    from unittest.mock import patch
    with patch("core.config.config") as mock_config:
        mock_config.db_ruta = ruta_temp
        mock_config.debug = False
        mock_config.tema = "oscuro"
        mock_config.usuario_nombre = "Usuario Test"
        mock_config.usuario_altura = 170
        mock_config.usuario_pasos_objetivo = 10000
        mock_config.usuario_agua_objetivo = 2.5
        mock_config.alertas_habilitadas = True
        mock_config.obtener = lambda key, default=None: default

        # Crear gestor con BD temporal
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models.base import Base

        engine = create_engine(f"sqlite:///{ruta_temp}")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)

        yield engine, SessionLocal


@pytest.fixture
def registro_base():
    """Datos de registro base para tests."""
    return {
        "fecha": date.today(),
        "periodo": "manana",
        "presion_sistolica": 120,
        "presion_diastolica": 80,
        "ritmo_cardiaco": 72,
        "oxigenacion": 98.0,
        "peso": 75.0,
        "pasos": 8000,
        "horas_sueno": 7.5,
        "calidad_sueno": 7,
        "nivel_estres": 4,
        "estado_animo": 7,
    }
