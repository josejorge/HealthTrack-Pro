"""
Servicio de registro de salud.

Orquesta la creación, actualización y consulta de registros,
calculando automáticamente el IMC e invocando el motor de alertas.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from database.connection import obtener_gestor
from database.repositories.registro_repository import RepositorioRegistro
from models.registro_salud import RegistroSalud
from core.config import config
from core.exceptions import DuplicadoError, RegistroNoEncontradoError

logger = logging.getLogger("healthtrack.services.registro")


class ServicioRegistro:
    """
    Servicio principal para gestionar registros de salud.

    Actúa como fachada entre la UI y el repositorio,
    aplicando reglas de negocio antes de persistir.
    """

    def __init__(self) -> None:
        self._gestor = obtener_gestor()

    # ──────────────────────────────────────────
    # Creación y actualización
    # ──────────────────────────────────────────

    def crear_registro(self, datos: dict[str, Any]) -> RegistroSalud:
        """
        Crea un nuevo registro de salud.

        Args:
            datos: Diccionario con los campos del registro.

        Returns:
            El RegistroSalud persistido con su ID asignado.

        Raises:
            DuplicadoError: Si ya existe un registro para esa fecha y período.
        """
        fecha: date = datos.get("fecha", date.today())
        periodo: str = datos.get("periodo", "manana")

        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)

            if repo.existe_para_fecha_y_periodo(fecha, periodo):
                raise DuplicadoError(fecha=fecha.isoformat(), periodo=periodo)

            registro = self._construir_registro(datos)
            repo.guardar(registro)
            logger.info(
                "Registro creado: fecha=%s, período=%s, ID=%s",
                fecha, periodo, registro.id
            )
            return registro

    def actualizar_registro(self, id_registro: int, datos: dict[str, Any]) -> RegistroSalud:
        """
        Actualiza un registro existente.

        Args:
            id_registro: ID del registro a modificar.
            datos: Campos a actualizar.

        Raises:
            RegistroNoEncontradoError: Si el ID no existe.
        """
        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)
            registro = repo.obtener_por_id(id_registro)

            if registro is None:
                raise RegistroNoEncontradoError(id_registro)

            self._aplicar_datos(registro, datos)
            registro.calcular_y_guardar_imc()
            repo.guardar(registro)
            logger.info("Registro actualizado: ID=%s", id_registro)
            return registro

    def guardar_o_actualizar(self, datos: dict[str, Any]) -> tuple[RegistroSalud, bool]:
        """
        Crea o actualiza según exista el registro para (fecha, periodo).

        Returns:
            Tupla (registro, creado) donde creado=True si fue nuevo.
        """
        fecha: date = datos.get("fecha", date.today())
        periodo: str = datos.get("periodo", "manana")

        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)
            existente = repo.obtener_por_fecha_y_periodo(fecha, periodo)

            if existente:
                self._aplicar_datos(existente, datos)
                existente.calcular_y_guardar_imc()
                repo.guardar(existente)
                return existente, False
            else:
                registro = self._construir_registro(datos)
                repo.guardar(registro)
                return registro, True

    def eliminar_registro(self, id_registro: int) -> bool:
        """Elimina un registro por ID. Devuelve True si fue encontrado."""
        with self._gestor.sesion() as sesion:
            repo = RepositorioRegistro(sesion)
            eliminado = repo.eliminar_por_id(id_registro)
            if eliminado:
                logger.info("Registro eliminado: ID=%s", id_registro)
            return eliminado

    # ──────────────────────────────────────────
    # Consultas
    # ──────────────────────────────────────────

    def obtener_por_id(self, id_registro: int) -> Optional[RegistroSalud]:
        with self._gestor.sesion() as sesion:
            return RepositorioRegistro(sesion).obtener_por_id(id_registro)

    def obtener_hoy(self) -> list[RegistroSalud]:
        """Devuelve los registros del día actual."""
        with self._gestor.sesion() as sesion:
            return RepositorioRegistro(sesion).obtener_por_fecha(date.today())

    def obtener_por_fecha(self, fecha: date) -> list[RegistroSalud]:
        with self._gestor.sesion() as sesion:
            return RepositorioRegistro(sesion).obtener_por_fecha(fecha)

    def obtener_ultimos_dias(self, dias: int = 7) -> list[RegistroSalud]:
        with self._gestor.sesion() as sesion:
            return RepositorioRegistro(sesion).obtener_ultimos_dias(dias)

    def obtener_recientes(self, limite: int = 20) -> list[RegistroSalud]:
        with self._gestor.sesion() as sesion:
            return RepositorioRegistro(sesion).obtener_recientes(limite)

    def obtener_ultimo(self) -> Optional[RegistroSalud]:
        with self._gestor.sesion() as sesion:
            return RepositorioRegistro(sesion).obtener_ultimo()

    def fechas_con_registros(self) -> list[date]:
        with self._gestor.sesion() as sesion:
            return RepositorioRegistro(sesion).fechas_con_registros()

    def total_registros(self) -> int:
        with self._gestor.sesion() as sesion:
            return RepositorioRegistro(sesion).contar()

    # ──────────────────────────────────────────
    # Helpers internos
    # ──────────────────────────────────────────

    @staticmethod
    def _construir_registro(datos: dict[str, Any]) -> RegistroSalud:
        """Construye un RegistroSalud desde un diccionario de datos."""
        altura = datos.get("altura") or config.usuario_altura
        registro = RegistroSalud(
            fecha=datos.get("fecha", date.today()),
            periodo=datos.get("periodo", "manana"),
            presion_sistolica=datos.get("presion_sistolica"),
            presion_diastolica=datos.get("presion_diastolica"),
            ritmo_cardiaco=datos.get("ritmo_cardiaco"),
            oxigenacion=datos.get("oxigenacion"),
            peso=datos.get("peso"),
            altura=altura,
            pasos=datos.get("pasos"),
            distancia_caminada=datos.get("distancia_caminada"),
            calorias_quemadas=datos.get("calorias_quemadas"),
            horas_sueno=datos.get("horas_sueno"),
            calidad_sueno=datos.get("calidad_sueno"),
            nivel_estres=datos.get("nivel_estres"),
            estado_animo=datos.get("estado_animo"),
            notas_medicas=datos.get("notas_medicas"),
            glucosa=datos.get("glucosa"),
            temperatura_corporal=datos.get("temperatura_corporal"),
            consumo_agua=datos.get("consumo_agua"),
            cafeina=datos.get("cafeina"),
            ejercicio_realizado=datos.get("ejercicio_realizado"),
        )
        # Medicamentos y síntomas como listas JSON
        if "medicamentos" in datos:
            registro.medicamentos_lista = datos["medicamentos"] or []
        if "sintomas" in datos:
            registro.sintomas_lista = datos["sintomas"] or []

        registro.calcular_y_guardar_imc()
        return registro

    @staticmethod
    def _aplicar_datos(registro: RegistroSalud, datos: dict[str, Any]) -> None:
        """Aplica los datos del diccionario sobre un registro existente."""
        campos = [
            "presion_sistolica", "presion_diastolica", "ritmo_cardiaco",
            "oxigenacion", "peso", "altura", "pasos", "distancia_caminada",
            "calorias_quemadas", "horas_sueno", "calidad_sueno", "nivel_estres",
            "estado_animo", "notas_medicas", "glucosa", "temperatura_corporal",
            "consumo_agua", "cafeina", "ejercicio_realizado",
        ]
        for campo in campos:
            if campo in datos:
                setattr(registro, campo, datos[campo])

        if "medicamentos" in datos:
            registro.medicamentos_lista = datos["medicamentos"] or []
        if "sintomas" in datos:
            registro.sintomas_lista = datos["sintomas"] or []
