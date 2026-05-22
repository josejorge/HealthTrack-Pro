"""
Modelo principal de registro de salud diario.

Almacena todas las métricas de salud que el usuario puede registrar
hasta tres veces al día (mañana, tarde, noche).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from core.constants import (
    CRITICIDAD_ATENCION,
    CRITICIDAD_CRITICO,
    CRITICIDAD_NORMAL,
    CRITICIDAD_PREOCUPANTE,
    IMC,
    OXIGENACION,
    PERIODOS_LISTA,
    PRESION_DIASTOLICA,
    PRESION_SISTOLICA,
    RITMO_CARDIACO,
)
from models.base import Base


class RegistroSalud(Base):
    """
    Registro completo de métricas de salud para un período del día.

    Restricción única: una sola entrada por (fecha, periodo).
    Calcula el IMC automáticamente al recibir peso y altura.
    """

    __tablename__ = "registros_salud"
    __table_args__ = (
        UniqueConstraint("fecha", "periodo", name="uq_fecha_periodo"),
    )

    # ──────────────────────────────────────────
    # Identificación
    # ──────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    periodo: Mapped[str] = mapped_column(String(10), nullable=False)

    # ──────────────────────────────────────────
    # Cardiovascular
    # ──────────────────────────────────────────
    presion_sistolica: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    presion_diastolica: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ritmo_cardiaco: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    oxigenacion: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ──────────────────────────────────────────
    # Física
    # ──────────────────────────────────────────
    peso: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    altura: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # cm
    imc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # calculado
    pasos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    distancia_caminada: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # km
    calorias_quemadas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ──────────────────────────────────────────
    # Descanso
    # ──────────────────────────────────────────
    horas_sueno: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calidad_sueno: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1–10

    # ──────────────────────────────────────────
    # Mental
    # ──────────────────────────────────────────
    nivel_estres: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 1–10
    estado_animo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 1–10

    # ──────────────────────────────────────────
    # Médica
    # ──────────────────────────────────────────
    medicamentos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # JSON list
    notas_medicas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sintomas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)       # JSON list

    # ──────────────────────────────────────────
    # Opcional / adicional
    # ──────────────────────────────────────────
    glucosa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)           # mg/dL
    temperatura_corporal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # °C
    consumo_agua: Mapped[Optional[float]] = mapped_column(Float, nullable=True)      # litros
    cafeina: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)           # mg
    ejercicio_realizado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ──────────────────────────────────────────
    # Auditoría
    # ──────────────────────────────────────────
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ──────────────────────────────────────────
    # Validaciones
    # ──────────────────────────────────────────

    @validates("periodo")
    def validar_periodo(self, _key: str, valor: str) -> str:
        if valor not in PERIODOS_LISTA:
            raise ValueError(f"Período inválido: '{valor}'. Use uno de: {PERIODOS_LISTA}")
        return valor

    @validates("presion_sistolica")
    def validar_sistolica(self, _key: str, valor: Optional[int]) -> Optional[int]:
        if valor is not None and not (60 <= valor <= 300):
            raise ValueError(f"Presión sistólica fuera de rango: {valor}")
        return valor

    @validates("presion_diastolica")
    def validar_diastolica(self, _key: str, valor: Optional[int]) -> Optional[int]:
        if valor is not None and not (40 <= valor <= 200):
            raise ValueError(f"Presión diastólica fuera de rango: {valor}")
        return valor

    @validates("ritmo_cardiaco")
    def validar_ritmo(self, _key: str, valor: Optional[int]) -> Optional[int]:
        if valor is not None and not (20 <= valor <= 300):
            raise ValueError(f"Ritmo cardíaco fuera de rango: {valor}")
        return valor

    @validates("oxigenacion")
    def validar_oxigenacion(self, _key: str, valor: Optional[float]) -> Optional[float]:
        if valor is not None and not (50.0 <= valor <= 100.0):
            raise ValueError(f"Oxigenación fuera de rango: {valor}")
        return valor

    @validates("calidad_sueno", "nivel_estres", "estado_animo")
    def validar_escala_1_10(self, key: str, valor: Optional[int]) -> Optional[int]:
        if valor is not None and not (1 <= valor <= 10):
            raise ValueError(f"'{key}' debe estar entre 1 y 10")
        return valor

    @validates("peso")
    def validar_peso(self, _key: str, valor: Optional[float]) -> Optional[float]:
        if valor is not None and not (1.0 <= valor <= 500.0):
            raise ValueError(f"Peso fuera de rango: {valor}")
        # Recalcular IMC cuando cambia el peso
        if valor is not None and self.altura:
            self.imc = self._calcular_imc(valor, self.altura)
        return valor

    @validates("altura")
    def validar_altura(self, _key: str, valor: Optional[float]) -> Optional[float]:
        if valor is not None and not (50.0 <= valor <= 300.0):
            raise ValueError(f"Altura fuera de rango: {valor}")
        if valor is not None and self.peso:
            self.imc = self._calcular_imc(self.peso, valor)
        return valor

    # ──────────────────────────────────────────
    # Métodos de cálculo
    # ──────────────────────────────────────────

    @staticmethod
    def _calcular_imc(peso_kg: float, altura_cm: float) -> float:
        """Calcula el Índice de Masa Corporal."""
        altura_m = altura_cm / 100.0
        if altura_m <= 0:
            return 0.0
        return round(peso_kg / (altura_m ** 2), 1)

    def calcular_y_guardar_imc(self) -> Optional[float]:
        """Calcula y almacena el IMC si hay peso y altura disponibles."""
        if self.peso and self.altura:
            self.imc = self._calcular_imc(self.peso, self.altura)
        return self.imc

    # ──────────────────────────────────────────
    # Clasificación de criticidad
    # ──────────────────────────────────────────

    def criticidad_presion(self) -> Optional[str]:
        """Clasifica la presión arterial según guías clínicas."""
        if self.presion_sistolica is None or self.presion_diastolica is None:
            return None
        s, d = self.presion_sistolica, self.presion_diastolica
        if s >= PRESION_SISTOLICA["crisis_min"] or d >= PRESION_DIASTOLICA["crisis_min"]:
            return CRITICIDAD_CRITICO
        if s >= PRESION_SISTOLICA["alta_2_min"] or d >= PRESION_DIASTOLICA["alta_2_min"]:
            return CRITICIDAD_PREOCUPANTE
        if s >= PRESION_SISTOLICA["alta_1_min"] or d >= PRESION_DIASTOLICA["alta_1_min"]:
            return CRITICIDAD_ATENCION
        return CRITICIDAD_NORMAL

    def criticidad_ritmo(self) -> Optional[str]:
        """Clasifica el ritmo cardíaco."""
        if self.ritmo_cardiaco is None:
            return None
        r = self.ritmo_cardiaco
        if r >= RITMO_CARDIACO["critico_min"] or r < 40:
            return CRITICIDAD_CRITICO
        if r >= RITMO_CARDIACO["taquicardia_min"] or r < RITMO_CARDIACO["bradicardia_max"]:
            return CRITICIDAD_ATENCION
        return CRITICIDAD_NORMAL

    def criticidad_oxigenacion(self) -> Optional[str]:
        """Clasifica la oxigenación en sangre."""
        if self.oxigenacion is None:
            return None
        o = self.oxigenacion
        if o <= OXIGENACION["critica_max"]:
            return CRITICIDAD_CRITICO
        if o < OXIGENACION["baja_min"]:
            return CRITICIDAD_PREOCUPANTE
        if o < OXIGENACION["normal_min"]:
            return CRITICIDAD_ATENCION
        return CRITICIDAD_NORMAL

    def criticidad_imc(self) -> Optional[str]:
        """Clasifica el IMC."""
        if self.imc is None:
            return None
        imc = self.imc
        if imc >= IMC["obesidad_min"]:
            return CRITICIDAD_PREOCUPANTE
        if imc >= IMC["sobrepeso_min"] or imc < IMC["normal_min"]:
            return CRITICIDAD_ATENCION
        return CRITICIDAD_NORMAL

    def criticidad_general(self) -> str:
        """
        Determina la criticidad global del registro.

        Devuelve el nivel más crítico entre todas las métricas registradas.
        """
        niveles = [
            self.criticidad_presion(),
            self.criticidad_ritmo(),
            self.criticidad_oxigenacion(),
            self.criticidad_imc(),
        ]
        niveles_validos = [n for n in niveles if n is not None]

        orden = [CRITICIDAD_CRITICO, CRITICIDAD_PREOCUPANTE, CRITICIDAD_ATENCION, CRITICIDAD_NORMAL]
        for nivel in orden:
            if nivel in niveles_validos:
                return nivel
        return CRITICIDAD_NORMAL

    # ──────────────────────────────────────────
    # Serialización
    # ──────────────────────────────────────────

    @property
    def medicamentos_lista(self) -> list[str]:
        """Devuelve la lista de medicamentos desde JSON."""
        if not self.medicamentos:
            return []
        try:
            return json.loads(self.medicamentos)
        except json.JSONDecodeError:
            return [self.medicamentos]

    @medicamentos_lista.setter
    def medicamentos_lista(self, valor: list[str]) -> None:
        self.medicamentos = json.dumps(valor, ensure_ascii=False)

    @property
    def sintomas_lista(self) -> list[str]:
        """Devuelve la lista de síntomas desde JSON."""
        if not self.sintomas:
            return []
        try:
            return json.loads(self.sintomas)
        except json.JSONDecodeError:
            return [self.sintomas]

    @sintomas_lista.setter
    def sintomas_lista(self, valor: list[str]) -> None:
        self.sintomas = json.dumps(valor, ensure_ascii=False)

    def to_dict(self) -> dict:
        """Serializa el registro a diccionario (para exportación y API)."""
        return {
            "id": self.id,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "periodo": self.periodo,
            "presion_sistolica": self.presion_sistolica,
            "presion_diastolica": self.presion_diastolica,
            "ritmo_cardiaco": self.ritmo_cardiaco,
            "oxigenacion": self.oxigenacion,
            "peso": self.peso,
            "altura": self.altura,
            "imc": self.imc,
            "pasos": self.pasos,
            "distancia_caminada": self.distancia_caminada,
            "calorias_quemadas": self.calorias_quemadas,
            "horas_sueno": self.horas_sueno,
            "calidad_sueno": self.calidad_sueno,
            "nivel_estres": self.nivel_estres,
            "estado_animo": self.estado_animo,
            "medicamentos": self.medicamentos_lista,
            "notas_medicas": self.notas_medicas,
            "sintomas": self.sintomas_lista,
            "glucosa": self.glucosa,
            "temperatura_corporal": self.temperatura_corporal,
            "consumo_agua": self.consumo_agua,
            "cafeina": self.cafeina,
            "ejercicio_realizado": self.ejercicio_realizado,
            "criticidad_general": self.criticidad_general(),
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }

    def __repr__(self) -> str:
        return (
            f"RegistroSalud(id={self.id}, fecha={self.fecha}, "
            f"periodo={self.periodo!r}, presion={self.presion_sistolica}/{self.presion_diastolica})"
        )
