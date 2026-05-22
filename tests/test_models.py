"""
Tests de los modelos SQLAlchemy de HealthTrack Pro.
"""

import pytest
from datetime import date

from models.registro_salud import RegistroSalud
from core.constants import (
    CRITICIDAD_NORMAL, CRITICIDAD_ATENCION,
    CRITICIDAD_PREOCUPANTE, CRITICIDAD_CRITICO,
)


class TestRegistroSalud:
    """Tests del modelo RegistroSalud."""

    def test_crear_registro_minimo(self):
        """Puede crear un registro con solo fecha y período."""
        registro = RegistroSalud(fecha=date.today(), periodo="manana")
        assert registro.fecha == date.today()
        assert registro.periodo == "manana"

    def test_periodo_invalido_lanza_error(self):
        """Un período inválido debe lanzar ValueError."""
        with pytest.raises(ValueError):
            RegistroSalud(fecha=date.today(), periodo="mediodia")

    def test_calculo_imc(self):
        """El IMC se calcula correctamente."""
        registro = RegistroSalud(fecha=date.today(), periodo="manana")
        imc = RegistroSalud._calcular_imc(75.0, 175.0)
        assert abs(imc - 24.5) < 0.1

    def test_criticidad_presion_normal(self):
        """Presión 115/75 debe ser NORMAL (ambos valores bajo los umbrales)."""
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            presion_sistolica=115, presion_diastolica=75,
        )
        assert registro.criticidad_presion() == CRITICIDAD_NORMAL

    def test_criticidad_presion_limite_normal(self):
        """Presión 120/80 es el umbral AHA — clasifica como ATENCIÓN."""
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            presion_sistolica=120, presion_diastolica=80,
        )
        # Sistólica 120 cae en alta_1_min (>=130) no, pero diastólica 80 = alta_1_min
        # Según AHA: sistólica 120-129 / diastólica <80 = "Elevada", no es alta_1
        # Pero 120/80 tiene diastólica=80 que es igual a alta_1_min=80 → ATENCION
        assert registro.criticidad_presion() == CRITICIDAD_ATENCION

    def test_criticidad_presion_atencion(self):
        """Presión 132/82 debe ser ATENCIÓN."""
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            presion_sistolica=132, presion_diastolica=82,
        )
        assert registro.criticidad_presion() == CRITICIDAD_ATENCION

    def test_criticidad_presion_preocupante(self):
        """Presión 145/95 debe ser PREOCUPANTE."""
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            presion_sistolica=145, presion_diastolica=95,
        )
        assert registro.criticidad_presion() == CRITICIDAD_PREOCUPANTE

    def test_criticidad_presion_critica(self):
        """Presión 185/125 debe ser CRÍTICO."""
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            presion_sistolica=185, presion_diastolica=125,
        )
        assert registro.criticidad_presion() == CRITICIDAD_CRITICO

    def test_criticidad_oxigenacion_normal(self):
        """SpO2 98% debe ser NORMAL."""
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            oxigenacion=98.0,
        )
        assert registro.criticidad_oxigenacion() == CRITICIDAD_NORMAL

    def test_criticidad_oxigenacion_critica(self):
        """SpO2 88% debe ser CRÍTICO."""
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            oxigenacion=88.0,
        )
        assert registro.criticidad_oxigenacion() == CRITICIDAD_CRITICO

    def test_medicamentos_como_lista(self):
        """Los medicamentos se serializan y deserializan como JSON."""
        registro = RegistroSalud(fecha=date.today(), periodo="manana")
        meds = ["Losartán 50mg", "Metformina 500mg"]
        registro.medicamentos_lista = meds
        assert registro.medicamentos_lista == meds

    def test_to_dict(self):
        """to_dict() devuelve un diccionario con todas las claves."""
        registro = RegistroSalud(
            fecha=date.today(), periodo="manana",
            presion_sistolica=120, presion_diastolica=80,
        )
        d = registro.to_dict()
        assert "fecha" in d
        assert "periodo" in d
        assert "presion_sistolica" in d
        assert d["presion_sistolica"] == 120

    def test_validacion_rango_presion(self):
        """Una presión sistólica fuera de rango lanza ValueError."""
        with pytest.raises(ValueError):
            RegistroSalud(
                fecha=date.today(), periodo="manana",
                presion_sistolica=500,  # Fuera de rango
            )

    def test_criticidad_general_sin_datos(self):
        """Un registro sin métricas devuelve criticidad normal."""
        registro = RegistroSalud(fecha=date.today(), periodo="manana")
        assert registro.criticidad_general() == CRITICIDAD_NORMAL
