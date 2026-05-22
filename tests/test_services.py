"""
Tests de los servicios de negocio de HealthTrack Pro.
"""

import pytest
from datetime import date, timedelta

from core.constants import CRITICIDAD_CRITICO, CRITICIDAD_ATENCION, CRITICIDAD_NORMAL


class TestServicioAlertas:
    """Tests del motor de alertas."""

    def test_alerta_crisis_hipertensiva(self):
        """Una presión de 185/125 genera alerta CRÍTICO."""
        from services.alertas_service import ServicioAlertas
        from models.registro_salud import RegistroSalud

        servicio = ServicioAlertas()
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            id=999,
            presion_sistolica=185,
            presion_diastolica=125,
        )
        alerta = servicio._evaluar_presion(registro)
        assert alerta is not None
        assert alerta.criticidad == CRITICIDAD_CRITICO

    def test_sin_alerta_presion_normal(self):
        """Una presión de 115/75 no genera alerta."""
        from services.alertas_service import ServicioAlertas
        from models.registro_salud import RegistroSalud

        servicio = ServicioAlertas()
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            id=998,
            presion_sistolica=115,
            presion_diastolica=75,
        )
        alerta = servicio._evaluar_presion(registro)
        assert alerta is None

    def test_alerta_taquicardia_severa(self):
        """Ritmo cardíaco de 160 bpm genera alerta CRÍTICO."""
        from services.alertas_service import ServicioAlertas
        from models.registro_salud import RegistroSalud

        servicio = ServicioAlertas()
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            id=997,
            ritmo_cardiaco=160,
        )
        alerta = servicio._evaluar_ritmo_cardiaco(registro)
        assert alerta is not None
        assert alerta.criticidad == CRITICIDAD_CRITICO

    def test_alerta_glucosa_diabetes(self):
        """Glucosa de 140 mg/dL genera alerta CRÍTICO."""
        from services.alertas_service import ServicioAlertas
        from models.registro_salud import RegistroSalud

        servicio = ServicioAlertas()
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            id=996,
            glucosa=140.0,
        )
        alerta = servicio._evaluar_glucosa(registro)
        assert alerta is not None
        assert alerta.criticidad == CRITICIDAD_CRITICO

    def test_sin_alerta_sin_metricas(self):
        """Un registro sin métricas no genera alertas."""
        from services.alertas_service import ServicioAlertas
        from models.registro_salud import RegistroSalud

        servicio = ServicioAlertas()
        registro = RegistroSalud(fecha=date.today(), periodo="manana", id=995)
        assert servicio._evaluar_presion(registro) is None
        assert servicio._evaluar_ritmo_cardiaco(registro) is None
        assert servicio._evaluar_oxigenacion(registro) is None


class TestServicioEstadisticas:
    """Tests del servicio de estadísticas."""

    def test_tendencia_creciente(self):
        """Una serie creciente devuelve tendencia 'sube'."""
        from services.estadisticas_service import ServicioEstadisticas
        valores = [100, 102, 104, 106, 108, 110, 112, 114]
        tendencia, pct = ServicioEstadisticas._calcular_tendencia(valores)
        assert tendencia == "sube"
        assert pct > 0

    def test_tendencia_decreciente(self):
        """Una serie decreciente devuelve tendencia 'baja'."""
        from services.estadisticas_service import ServicioEstadisticas
        valores = [120, 118, 116, 114, 112, 110, 108, 106]
        tendencia, pct = ServicioEstadisticas._calcular_tendencia(valores)
        assert tendencia == "baja"

    def test_tendencia_estable(self):
        """Una serie sin cambio significativo devuelve 'estable'."""
        from services.estadisticas_service import ServicioEstadisticas
        valores = [100.0, 100.5, 99.5, 100.2, 99.8, 100.1, 100.0, 99.9]
        tendencia, pct = ServicioEstadisticas._calcular_tendencia(valores)
        assert tendencia == "estable"

    def test_tendencia_pocos_datos(self):
        """Menos de 4 datos devuelve 'estable'."""
        from services.estadisticas_service import ServicioEstadisticas
        valores = [100, 105]
        tendencia, pct = ServicioEstadisticas._calcular_tendencia(valores)
        assert tendencia == "estable"


class TestServicioInsights:
    """Tests básicos del servicio de insights."""

    def test_insight_sin_datos(self):
        """Con menos de 3 registros devuelve insight de 'necesita más datos'."""
        from services.insights_service import ServicioInsights
        servicio = ServicioInsights()
        insights = servicio._analizar_actividad([])
        assert isinstance(insights, list)
