"""
Motor de alertas de salud.

Evalúa cada registro contra umbrales clínicos y genera alertas
clasificadas por criticidad con recomendaciones personalizadas.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from database.connection import obtener_gestor
from database.repositories.alerta_repository import RepositorioAlerta
from database.repositories.registro_repository import RepositorioRegistro
from models.alerta import Alerta
from models.registro_salud import RegistroSalud
from core.constants import (
    CRITICIDAD_ATENCION,
    CRITICIDAD_CRITICO,
    CRITICIDAD_NORMAL,
    CRITICIDAD_PREOCUPANTE,
    GLUCOSA,
    OXIGENACION,
    PRESION_DIASTOLICA,
    PRESION_SISTOLICA,
    RITMO_CARDIACO,
    TEMPERATURA,
    SUENO,
    ESCALA_ESTRES,
)

logger = logging.getLogger("healthtrack.services.alertas")


class ServicioAlertas:
    """
    Motor de reglas clínicas para detección de valores anómalos.

    Evalúa un RegistroSalud y produce Alertas con criticidad,
    descripción y recomendación en lenguaje natural.
    """

    def __init__(self) -> None:
        self._gestor = obtener_gestor()

    # ──────────────────────────────────────────
    # Evaluación completa de un registro
    # ──────────────────────────────────────────

    def evaluar_registro(self, registro: RegistroSalud) -> list[Alerta]:
        """
        Evalúa un registro y persiste las alertas generadas.

        Args:
            registro: El registro recién guardado a analizar.

        Returns:
            Lista de Alertas creadas (pueden ser ninguna si todo es normal).
        """
        alertas_generadas: list[Alerta] = []

        evaluadores = [
            self._evaluar_presion,
            self._evaluar_ritmo_cardiaco,
            self._evaluar_oxigenacion,
            self._evaluar_glucosa,
            self._evaluar_temperatura,
            self._evaluar_sueno,
            self._evaluar_estres,
        ]

        for evaluador in evaluadores:
            alerta = evaluador(registro)
            if alerta:
                alertas_generadas.append(alerta)

        if alertas_generadas:
            with self._gestor.sesion() as sesion:
                repo = RepositorioAlerta(sesion)
                for alerta in alertas_generadas:
                    repo.guardar(alerta)

            logger.info(
                "Registro ID=%s — %d alertas generadas",
                registro.id,
                len(alertas_generadas),
            )

        return alertas_generadas

    # ──────────────────────────────────────────
    # Consulta de alertas
    # ──────────────────────────────────────────

    def obtener_alertas_activas(self) -> list[Alerta]:
        """Devuelve todas las alertas no resueltas."""
        with self._gestor.sesion() as sesion:
            return RepositorioAlerta(sesion).obtener_activas()

    def obtener_no_vistas(self) -> list[Alerta]:
        """Devuelve alertas pendientes de revisar por el usuario."""
        with self._gestor.sesion() as sesion:
            return RepositorioAlerta(sesion).obtener_no_vistas()

    def contar_no_vistas(self) -> int:
        with self._gestor.sesion() as sesion:
            return RepositorioAlerta(sesion).contar_no_vistas()

    def marcar_todas_vistas(self) -> int:
        with self._gestor.sesion() as sesion:
            return RepositorioAlerta(sesion).marcar_todas_vistas()

    # ──────────────────────────────────────────
    # Evaluadores por métrica
    # ──────────────────────────────────────────

    def _evaluar_presion(self, registro: RegistroSalud) -> Optional[Alerta]:
        """Evalúa presión arterial según guías AHA/ESC."""
        s = registro.presion_sistolica
        d = registro.presion_diastolica

        if s is None or d is None:
            return None

        if s >= PRESION_SISTOLICA["crisis_min"] or d >= PRESION_DIASTOLICA["crisis_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="presion_arterial",
                valor=f"{s}/{d} mmHg",
                criticidad=CRITICIDAD_CRITICO,
                titulo="Crisis hipertensiva detectada",
                descripcion=(
                    f"Tu presión arterial de {s}/{d} mmHg está en niveles de crisis "
                    "(sistólica ≥ 180 o diastólica ≥ 120 mmHg)."
                ),
                recomendacion=(
                    "Busca atención médica de urgencia inmediatamente. "
                    "No realices esfuerzo físico y mantén la calma."
                ),
            )

        if s >= PRESION_SISTOLICA["alta_2_min"] or d >= PRESION_DIASTOLICA["alta_2_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="presion_arterial",
                valor=f"{s}/{d} mmHg",
                criticidad=CRITICIDAD_PREOCUPANTE,
                titulo="Hipertensión arterial grado 2",
                descripcion=f"Presión arterial elevada: {s}/{d} mmHg.",
                recomendacion="Consulta a tu médico. Reduce el sodio y el estrés.",
            )

        if s >= PRESION_SISTOLICA["alta_1_min"] or d >= PRESION_DIASTOLICA["alta_1_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="presion_arterial",
                valor=f"{s}/{d} mmHg",
                criticidad=CRITICIDAD_ATENCION,
                titulo="Presión arterial ligeramente elevada",
                descripcion=f"Presión arterial: {s}/{d} mmHg (Hipertensión grado 1).",
                recomendacion=(
                    "Monitorea más frecuentemente. Reduce el consumo de sal, "
                    "haz ejercicio moderado y limita el alcohol."
                ),
            )

        return None

    def _evaluar_ritmo_cardiaco(self, registro: RegistroSalud) -> Optional[Alerta]:
        """Evalúa el ritmo cardíaco."""
        r = registro.ritmo_cardiaco
        if r is None:
            return None

        if r >= RITMO_CARDIACO["critico_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="ritmo_cardiaco",
                valor=f"{r} bpm",
                criticidad=CRITICIDAD_CRITICO,
                titulo="Taquicardia severa",
                descripcion=f"Ritmo cardíaco de {r} bpm — significativamente elevado.",
                recomendacion="Busca atención médica urgente. Reposa y evita esfuerzos.",
            )

        if r >= RITMO_CARDIACO["taquicardia_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="ritmo_cardiaco",
                valor=f"{r} bpm",
                criticidad=CRITICIDAD_ATENCION,
                titulo="Frecuencia cardíaca elevada",
                descripcion=f"Ritmo cardíaco: {r} bpm (taquicardia leve).",
                recomendacion="Descansa, hidrárate y evita la cafeína.",
            )

        if r <= RITMO_CARDIACO["bradicardia_max"] and r > 40:
            return self._crear_alerta(
                registro=registro,
                metrica="ritmo_cardiaco",
                valor=f"{r} bpm",
                criticidad=CRITICIDAD_ATENCION,
                titulo="Frecuencia cardíaca baja",
                descripcion=f"Ritmo cardíaco: {r} bpm (bradicardia).",
                recomendacion="Consulta a tu médico si presentas mareos o fatiga.",
            )

        if r <= 40:
            return self._crear_alerta(
                registro=registro,
                metrica="ritmo_cardiaco",
                valor=f"{r} bpm",
                criticidad=CRITICIDAD_CRITICO,
                titulo="Bradicardia severa",
                descripcion=f"Ritmo cardíaco de {r} bpm — peligrosamente bajo.",
                recomendacion="Acude a urgencias de inmediato.",
            )

        return None

    def _evaluar_oxigenacion(self, registro: RegistroSalud) -> Optional[Alerta]:
        """Evalúa la saturación de oxígeno en sangre."""
        o = registro.oxigenacion
        if o is None:
            return None

        if o < OXIGENACION["baja_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="oxigenacion",
                valor=f"{o}%",
                criticidad=CRITICIDAD_CRITICO,
                titulo="Oxigenación críticamente baja",
                descripcion=f"SpO2 de {o}% — hipoxia severa.",
                recomendacion="Busca atención médica urgente inmediatamente.",
            )

        if o < OXIGENACION["normal_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="oxigenacion",
                valor=f"{o}%",
                criticidad=CRITICIDAD_PREOCUPANTE,
                titulo="Oxigenación baja",
                descripcion=f"SpO2 de {o}% — por debajo del rango normal (95–100%).",
                recomendacion="Respira profundamente. Consulta a tu médico si persiste.",
            )

        return None

    def _evaluar_glucosa(self, registro: RegistroSalud) -> Optional[Alerta]:
        """Evalúa el nivel de glucosa en sangre."""
        g = registro.glucosa
        if g is None:
            return None

        if g >= GLUCOSA["diabetes_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="glucosa",
                valor=f"{g} mg/dL",
                criticidad=CRITICIDAD_CRITICO,
                titulo="Glucosa en nivel diabético",
                descripcion=f"Glucosa de {g} mg/dL — rango de diabetes.",
                recomendacion="Consulta a tu médico de inmediato.",
            )

        if g >= GLUCOSA["prediabetes_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="glucosa",
                valor=f"{g} mg/dL",
                criticidad=CRITICIDAD_ATENCION,
                titulo="Glucosa en rango de prediabetes",
                descripcion=f"Glucosa de {g} mg/dL — prediabetes ({GLUCOSA['prediabetes_min']}–{GLUCOSA['prediabetes_max']} mg/dL).",
                recomendacion="Reduce azúcares y carbohidratos refinados. Ejercicio regular.",
            )

        if g <= GLUCOSA["hipoglucemia_max"]:
            return self._crear_alerta(
                registro=registro,
                metrica="glucosa",
                valor=f"{g} mg/dL",
                criticidad=CRITICIDAD_PREOCUPANTE,
                titulo="Hipoglucemia detectada",
                descripcion=f"Glucosa de {g} mg/dL — por debajo de 70 mg/dL.",
                recomendacion="Consume algo dulce de acción rápida. Consulta si se repite.",
            )

        return None

    def _evaluar_temperatura(self, registro: RegistroSalud) -> Optional[Alerta]:
        """Evalúa la temperatura corporal."""
        t = registro.temperatura_corporal
        if t is None:
            return None

        if t >= TEMPERATURA["critica_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="temperatura_corporal",
                valor=f"{t}°C",
                criticidad=CRITICIDAD_CRITICO,
                titulo="Fiebre muy alta",
                descripcion=f"Temperatura de {t}°C — fiebre peligrosa.",
                recomendacion="Acude a urgencias. Aplica medidas para bajar la fiebre.",
            )

        if t >= TEMPERATURA["fiebre_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="temperatura_corporal",
                valor=f"{t}°C",
                criticidad=CRITICIDAD_PREOCUPANTE,
                titulo="Fiebre detectada",
                descripcion=f"Temperatura de {t}°C.",
                recomendacion="Hidrárate, descansa y toma antipirético si es necesario.",
            )

        if t <= TEMPERATURA["hipotermia_max"]:
            return self._crear_alerta(
                registro=registro,
                metrica="temperatura_corporal",
                valor=f"{t}°C",
                criticidad=CRITICIDAD_PREOCUPANTE,
                titulo="Temperatura corporal baja",
                descripcion=f"Temperatura de {t}°C — posible hipotermia leve.",
                recomendacion="Caliéntate y consulta si los síntomas persisten.",
            )

        return None

    def _evaluar_sueno(self, registro: RegistroSalud) -> Optional[Alerta]:
        """Evalúa la calidad y duración del sueño."""
        h = registro.horas_sueno
        if h is None:
            return None

        if h < SUENO["insuficiente_max"]:
            return self._crear_alerta(
                registro=registro,
                metrica="horas_sueno",
                valor=f"{h}h",
                criticidad=CRITICIDAD_ATENCION,
                titulo="Sueño insuficiente",
                descripcion=f"Solo {h} horas de sueño — la recomendación es 7–9 horas.",
                recomendacion="Establece una rutina de sueño regular. Evita pantallas antes de dormir.",
            )

        return None

    def _evaluar_estres(self, registro: RegistroSalud) -> Optional[Alerta]:
        """Evalúa el nivel de estrés reportado."""
        e = registro.nivel_estres
        if e is None:
            return None

        if e >= ESCALA_ESTRES["muy_alto_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="nivel_estres",
                valor=f"{e}/10",
                criticidad=CRITICIDAD_PREOCUPANTE,
                titulo="Nivel de estrés muy alto",
                descripcion=f"Estrés reportado: {e}/10.",
                recomendacion="Practica técnicas de relajación, meditación o ejercicio.",
            )

        if e >= ESCALA_ESTRES["alto_min"]:
            return self._crear_alerta(
                registro=registro,
                metrica="nivel_estres",
                valor=f"{e}/10",
                criticidad=CRITICIDAD_ATENCION,
                titulo="Nivel de estrés elevado",
                descripcion=f"Estrés reportado: {e}/10.",
                recomendacion="Toma descansos regulares y practica respiración profunda.",
            )

        return None

    # ──────────────────────────────────────────
    # Helper de construcción
    # ──────────────────────────────────────────

    @staticmethod
    def _crear_alerta(
        registro: RegistroSalud,
        metrica: str,
        valor: str,
        criticidad: str,
        titulo: str,
        descripcion: str,
        recomendacion: str,
    ) -> Alerta:
        return Alerta(
            registro_id=registro.id,
            fecha=registro.fecha,
            metrica=metrica,
            valor=valor,
            criticidad=criticidad,
            titulo=titulo,
            descripcion=descripcion,
            recomendacion=recomendacion,
        )
