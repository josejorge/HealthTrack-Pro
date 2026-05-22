"""
Formulario de registro de métricas de salud.

Permite al usuario ingresar todas sus métricas de salud
para un período del día (mañana, tarde, noche).
Valida, calcula el IMC y persiste el registro.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.registro_service import ServicioRegistro
from services.alertas_service import ServicioAlertas
from core.config import config
from core.constants import PERIODOS, PERIODOS_LISTA
from core.exceptions import DuplicadoError

logger = logging.getLogger("healthtrack.ui.registro")


def _crear_etiqueta(texto: str, tooltip: str = "") -> QLabel:
    """Crea una etiqueta de campo de formulario con tooltip opcional."""
    lbl = QLabel(texto)
    lbl.setObjectName("etiqueta_campo")
    if tooltip:
        lbl.setToolTip(tooltip)
    return lbl


def _crear_spin_entero(minimo: int, maximo: int, paso: int = 1, sufijo: str = "") -> QSpinBox:
    """Crea un QSpinBox configurado."""
    spin = QSpinBox()
    spin.setRange(minimo, maximo)
    spin.setSingleStep(paso)
    spin.setSpecialValueText("—")
    spin.setValue(minimo - 1 if minimo > 0 else minimo)
    if sufijo:
        spin.setSuffix(f" {sufijo}")
    return spin


def _crear_spin_decimal(
    minimo: float, maximo: float, decimales: int = 1,
    paso: float = 0.1, sufijo: str = ""
) -> QDoubleSpinBox:
    """Crea un QDoubleSpinBox configurado."""
    spin = QDoubleSpinBox()
    spin.setRange(minimo, maximo)
    spin.setDecimals(decimales)
    spin.setSingleStep(paso)
    spin.setSpecialValueText("—")
    spin.setValue(minimo - paso)
    if sufijo:
        spin.setSuffix(f" {sufijo}")
    return spin


class SliderConEtiqueta(QWidget):
    """Control deslizante 1–10 con etiqueta de valor en tiempo real."""

    value_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 10)
        self._slider.setValue(0)
        self._slider.setTickInterval(1)
        self._slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self._lbl_valor = QLabel("—")
        self._lbl_valor.setFixedWidth(28)
        self._lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_valor.setStyleSheet("font-weight: bold; font-size: 14px;")

        self._slider.valueChanged.connect(self._on_value_changed)

        layout.addWidget(self._slider)
        layout.addWidget(self._lbl_valor)

    def _on_value_changed(self, valor: int) -> None:
        texto = str(valor) if valor > 0 else "—"
        self._lbl_valor.setText(texto)
        self.value_changed.emit(valor)

    def value(self) -> Optional[int]:
        v = self._slider.value()
        return v if v > 0 else None

    def setValue(self, valor: Optional[int]) -> None:
        self._slider.setValue(valor or 0)


class RegistroWidget(QWidget):
    """
    Formulario completo de registro de salud.

    Organizado en secciones (GroupBox) con todos los campos
    posibles. Los campos vacíos (spin en valor especial) no se guardan.

    Señales:
        registro_guardado: Emitida tras persistir un registro nuevo o actualizado.
    """

    registro_guardado = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._servicio_registro = ServicioRegistro()
        self._servicio_alertas = ServicioAlertas()
        self._registro_id: Optional[int] = None  # None = nuevo registro

        self._construir_ui()

    # ──────────────────────────────────────────
    # Construcción de la UI
    # ──────────────────────────────────────────

    def _construir_ui(self) -> None:
        """Construye el formulario completo con scroll."""
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        contenedor = QWidget()
        scroll.setWidget(contenedor)

        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        # ── Encabezado ────────────────────────────
        layout.addLayout(self._crear_encabezado())

        # ── Fecha y período ───────────────────────
        layout.addWidget(self._crear_grupo_fecha())

        # ── Secciones de métricas ─────────────────
        grid_grupos = QGridLayout()
        grid_grupos.setSpacing(16)

        grid_grupos.addWidget(self._crear_grupo_cardiovascular(), 0, 0)
        grid_grupos.addWidget(self._crear_grupo_fisica(), 0, 1)
        grid_grupos.addWidget(self._crear_grupo_descanso(), 1, 0)
        grid_grupos.addWidget(self._crear_grupo_mental(), 1, 1)
        grid_grupos.addWidget(self._crear_grupo_medica(), 2, 0)
        grid_grupos.addWidget(self._crear_grupo_opcional(), 2, 1)

        layout.addLayout(grid_grupos)

        # ── Botones ───────────────────────────────
        layout.addLayout(self._crear_botones())
        layout.addStretch()

        layout_externo = QVBoxLayout(self)
        layout_externo.setContentsMargins(0, 0, 0, 0)
        layout_externo.addWidget(scroll)

    def _crear_encabezado(self) -> QHBoxLayout:
        fila = QHBoxLayout()
        titulo = QLabel("Nuevo Registro de Salud")
        titulo.setObjectName("titulo_seccion")
        subtitulo = QLabel("Completa los campos disponibles. Los vacíos se omitirán.")
        subtitulo.setObjectName("subtitulo_seccion")
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(titulo)
        col.addWidget(subtitulo)
        fila.addLayout(col)
        fila.addStretch()
        return fila

    def _crear_grupo_fecha(self) -> QGroupBox:
        """Selección de fecha y período del día."""
        grupo = QGroupBox("  Identificación del Registro")
        layout = QHBoxLayout(grupo)
        layout.setSpacing(20)

        # Fecha
        col_fecha = QVBoxLayout()
        col_fecha.addWidget(_crear_etiqueta("Fecha de registro"))
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_edit.setFixedWidth(140)
        col_fecha.addWidget(self._date_edit)
        layout.addLayout(col_fecha)

        # Período
        col_periodo = QVBoxLayout()
        col_periodo.addWidget(_crear_etiqueta("Período del día"))
        self._combo_periodo = QComboBox()
        for key, label in PERIODOS.items():
            self._combo_periodo.addItem(label, key)
        self._combo_periodo.setFixedWidth(140)
        col_periodo.addWidget(self._combo_periodo)
        layout.addLayout(col_periodo)

        layout.addStretch()
        return grupo

    def _crear_grupo_cardiovascular(self) -> QGroupBox:
        """Campos cardiovasculares."""
        grupo = QGroupBox("  ❤️  Cardiovascular")
        layout = QGridLayout(grupo)
        layout.setSpacing(10)

        # Presión sistólica
        layout.addWidget(_crear_etiqueta("Presión sistólica", "Valor superior de la presión (mmHg)"), 0, 0)
        self._spin_sistolica = _crear_spin_entero(60, 300, 1, "mmHg")
        layout.addWidget(self._spin_sistolica, 1, 0)

        # Presión diastólica
        layout.addWidget(_crear_etiqueta("Presión diastólica", "Valor inferior de la presión (mmHg)"), 0, 1)
        self._spin_diastolica = _crear_spin_entero(40, 200, 1, "mmHg")
        layout.addWidget(self._spin_diastolica, 1, 1)

        # Ritmo cardíaco
        layout.addWidget(_crear_etiqueta("Ritmo cardíaco", "Pulsaciones por minuto"), 2, 0)
        self._spin_ritmo = _crear_spin_entero(20, 300, 1, "bpm")
        layout.addWidget(self._spin_ritmo, 3, 0)

        # SpO2
        layout.addWidget(_crear_etiqueta("Oxigenación SpO2", "Saturación de oxígeno en sangre (%)"), 2, 1)
        self._spin_spo2 = _crear_spin_decimal(50.0, 100.0, 1, 0.5, "%")
        layout.addWidget(self._spin_spo2, 3, 1)

        return grupo

    def _crear_grupo_fisica(self) -> QGroupBox:
        """Campos de información física."""
        grupo = QGroupBox("  🏋️  Información Física")
        layout = QGridLayout(grupo)
        layout.setSpacing(10)

        layout.addWidget(_crear_etiqueta("Peso (kg)"), 0, 0)
        self._spin_peso = _crear_spin_decimal(1.0, 500.0, 1, 0.1, "kg")
        layout.addWidget(self._spin_peso, 1, 0)

        # IMC calculado (solo lectura)
        layout.addWidget(_crear_etiqueta("IMC (calculado automáticamente)"), 0, 1)
        self._lbl_imc = QLabel("—")
        self._lbl_imc.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        layout.addWidget(self._lbl_imc, 1, 1)

        layout.addWidget(_crear_etiqueta("Pasos"), 2, 0)
        self._spin_pasos = _crear_spin_entero(0, 100000, 100, "pasos")
        layout.addWidget(self._spin_pasos, 3, 0)

        layout.addWidget(_crear_etiqueta("Distancia (km)"), 2, 1)
        self._spin_distancia = _crear_spin_decimal(0.0, 200.0, 1, 0.1, "km")
        layout.addWidget(self._spin_distancia, 3, 1)

        layout.addWidget(_crear_etiqueta("Calorías quemadas"), 4, 0)
        self._spin_calorias = _crear_spin_entero(0, 10000, 10, "kcal")
        layout.addWidget(self._spin_calorias, 5, 0)

        # Conectar para calcular IMC
        self._spin_peso.valueChanged.connect(self._calcular_imc_ui)

        return grupo

    def _crear_grupo_descanso(self) -> QGroupBox:
        """Campos de descanso y sueño."""
        grupo = QGroupBox("  😴  Descanso")
        layout = QGridLayout(grupo)
        layout.setSpacing(10)

        layout.addWidget(_crear_etiqueta("Horas de sueño"), 0, 0)
        self._spin_sueno = _crear_spin_decimal(0.0, 24.0, 1, 0.5, "h")
        layout.addWidget(self._spin_sueno, 1, 0)

        layout.addWidget(_crear_etiqueta("Calidad del sueño (1–10)"), 2, 0, 1, 2)
        self._slider_calidad_sueno = SliderConEtiqueta()
        layout.addWidget(self._slider_calidad_sueno, 3, 0, 1, 2)

        return grupo

    def _crear_grupo_mental(self) -> QGroupBox:
        """Campos de estado mental y emocional."""
        grupo = QGroupBox("  🧠  Estado Mental")
        layout = QGridLayout(grupo)
        layout.setSpacing(10)

        layout.addWidget(_crear_etiqueta("Nivel de estrés (1–10)"), 0, 0, 1, 2)
        self._slider_estres = SliderConEtiqueta()
        layout.addWidget(self._slider_estres, 1, 0, 1, 2)

        layout.addWidget(_crear_etiqueta("Estado de ánimo (1–10)"), 2, 0, 1, 2)
        self._slider_animo = SliderConEtiqueta()
        layout.addWidget(self._slider_animo, 3, 0, 1, 2)

        return grupo

    def _crear_grupo_medica(self) -> QGroupBox:
        """Campos de información médica."""
        grupo = QGroupBox("  💊  Información Médica")
        layout = QVBoxLayout(grupo)
        layout.setSpacing(10)

        layout.addWidget(_crear_etiqueta("Medicamentos tomados hoy"))
        self._txt_medicamentos = QTextEdit()
        self._txt_medicamentos.setPlaceholderText("Ej: Losartán 50mg, Metformina 500mg…")
        self._txt_medicamentos.setMaximumHeight(70)
        layout.addWidget(self._txt_medicamentos)

        layout.addWidget(_crear_etiqueta("Síntomas"))
        self._txt_sintomas = QTextEdit()
        self._txt_sintomas.setPlaceholderText("Ej: Dolor de cabeza, mareos leves…")
        self._txt_sintomas.setMaximumHeight(70)
        layout.addWidget(self._txt_sintomas)

        layout.addWidget(_crear_etiqueta("Notas médicas"))
        self._txt_notas = QTextEdit()
        self._txt_notas.setPlaceholderText("Observaciones, visitas médicas, resultados…")
        self._txt_notas.setMaximumHeight(80)
        layout.addWidget(self._txt_notas)

        return grupo

    def _crear_grupo_opcional(self) -> QGroupBox:
        """Campos adicionales opcionales."""
        grupo = QGroupBox("  📋  Datos Adicionales")
        layout = QGridLayout(grupo)
        layout.setSpacing(10)

        layout.addWidget(_crear_etiqueta("Glucosa", "Nivel de azúcar en sangre (mg/dL)"), 0, 0)
        self._spin_glucosa = _crear_spin_decimal(0.0, 800.0, 1, 1.0, "mg/dL")
        layout.addWidget(self._spin_glucosa, 1, 0)

        layout.addWidget(_crear_etiqueta("Temperatura corporal"), 0, 1)
        self._spin_temperatura = _crear_spin_decimal(30.0, 45.0, 1, 0.1, "°C")
        layout.addWidget(self._spin_temperatura, 1, 1)

        layout.addWidget(_crear_etiqueta("Consumo de agua"), 2, 0)
        self._spin_agua = _crear_spin_decimal(0.0, 20.0, 1, 0.25, "L")
        layout.addWidget(self._spin_agua, 3, 0)

        layout.addWidget(_crear_etiqueta("Cafeína consumida"), 2, 1)
        self._spin_cafeina = _crear_spin_entero(0, 2000, 25, "mg")
        layout.addWidget(self._spin_cafeina, 3, 1)

        layout.addWidget(_crear_etiqueta("Ejercicio realizado"), 4, 0, 1, 2)
        self._txt_ejercicio = QTextEdit()
        self._txt_ejercicio.setPlaceholderText("Ej: Caminata 30 min, Yoga 45 min…")
        self._txt_ejercicio.setMaximumHeight(60)
        layout.addWidget(self._txt_ejercicio, 5, 0, 1, 2)

        return grupo

    def _crear_botones(self) -> QHBoxLayout:
        """Fila de botones de acción."""
        fila = QHBoxLayout()
        fila.setSpacing(12)
        fila.addStretch()

        self._btn_limpiar = QPushButton("Limpiar Formulario")
        self._btn_limpiar.setObjectName("btn_secundario")
        self._btn_limpiar.setFixedHeight(42)
        self._btn_limpiar.setFixedWidth(180)
        self._btn_limpiar.clicked.connect(self.limpiar_formulario)

        self._btn_guardar = QPushButton("✓  Guardar Registro")
        self._btn_guardar.setObjectName("btn_primario")
        self._btn_guardar.setFixedHeight(42)
        self._btn_guardar.setFixedWidth(200)
        self._btn_guardar.clicked.connect(self._guardar)

        fila.addWidget(self._btn_limpiar)
        fila.addWidget(self._btn_guardar)
        return fila

    # ──────────────────────────────────────────
    # Lógica del formulario
    # ──────────────────────────────────────────

    def _calcular_imc_ui(self) -> None:
        """Actualiza la etiqueta de IMC en tiempo real."""
        peso = self._spin_peso.value()
        altura = config.usuario_altura
        if peso > 0 and altura > 0:
            altura_m = altura / 100
            imc = round(peso / (altura_m ** 2), 1)
            # Color según categoría
            if imc < 18.5:
                color = "#3b82f6"
                cat = "Bajo peso"
            elif imc < 25:
                color = "#22c55e"
                cat = "Normal"
            elif imc < 30:
                color = "#f59e0b"
                cat = "Sobrepeso"
            else:
                color = "#ef4444"
                cat = "Obesidad"
            self._lbl_imc.setText(f"{imc}")
            self._lbl_imc.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color}; padding: 8px;")
            self._lbl_imc.setToolTip(f"IMC: {imc} — {cat}")
        else:
            self._lbl_imc.setText("—")

    def _recopilar_datos(self) -> dict[str, Any]:
        """Lee todos los campos del formulario y devuelve un diccionario."""

        def spin_valor_entero(spin: QSpinBox) -> Optional[int]:
            v = spin.value()
            return v if v > spin.minimum() else None

        def spin_valor_decimal(spin: QDoubleSpinBox) -> Optional[float]:
            v = spin.value()
            return v if v > spin.minimum() else None

        q_date = self._date_edit.date()
        fecha = date(q_date.year(), q_date.month(), q_date.day())
        periodo = self._combo_periodo.currentData()

        medicamentos_texto = self._txt_medicamentos.toPlainText().strip()
        medicamentos = [m.strip() for m in medicamentos_texto.split(",") if m.strip()] if medicamentos_texto else []

        sintomas_texto = self._txt_sintomas.toPlainText().strip()
        sintomas = [s.strip() for s in sintomas_texto.split(",") if s.strip()] if sintomas_texto else []

        return {
            "fecha": fecha,
            "periodo": periodo,
            "presion_sistolica": spin_valor_entero(self._spin_sistolica),
            "presion_diastolica": spin_valor_entero(self._spin_diastolica),
            "ritmo_cardiaco": spin_valor_entero(self._spin_ritmo),
            "oxigenacion": spin_valor_decimal(self._spin_spo2),
            "peso": spin_valor_decimal(self._spin_peso),
            "pasos": spin_valor_entero(self._spin_pasos),
            "distancia_caminada": spin_valor_decimal(self._spin_distancia),
            "calorias_quemadas": spin_valor_entero(self._spin_calorias),
            "horas_sueno": spin_valor_decimal(self._spin_sueno),
            "calidad_sueno": self._slider_calidad_sueno.value(),
            "nivel_estres": self._slider_estres.value(),
            "estado_animo": self._slider_animo.value(),
            "medicamentos": medicamentos,
            "sintomas": sintomas,
            "notas_medicas": self._txt_notas.toPlainText().strip() or None,
            "glucosa": spin_valor_decimal(self._spin_glucosa),
            "temperatura_corporal": spin_valor_decimal(self._spin_temperatura),
            "consumo_agua": spin_valor_decimal(self._spin_agua),
            "cafeina": spin_valor_entero(self._spin_cafeina),
            "ejercicio_realizado": self._txt_ejercicio.toPlainText().strip() or None,
        }

    def _guardar(self) -> None:
        """Recopila datos, valida y guarda el registro."""
        datos = self._recopilar_datos()

        # Verificar que haya al menos un campo con dato
        campos_obligatorios = [
            "presion_sistolica", "ritmo_cardiaco", "oxigenacion",
            "peso", "pasos", "horas_sueno",
        ]
        if not any(datos.get(c) is not None for c in campos_obligatorios):
            QMessageBox.warning(
                self,
                "Sin datos",
                "Por favor ingresa al menos una métrica de salud antes de guardar.",
            )
            return

        try:
            registro, creado = self._servicio_registro.guardar_o_actualizar(datos)

            # Evaluar alertas en el nuevo registro
            try:
                self._servicio_alertas.evaluar_registro(registro)
            except Exception as e:
                logger.warning("Error al evaluar alertas: %s", e)

            accion = "creado" if creado else "actualizado"
            QMessageBox.information(
                self,
                "Registro guardado",
                f"✓  Registro {accion} correctamente para "
                f"{datos['fecha'].strftime('%d/%m/%Y')} — "
                f"{PERIODOS.get(datos['periodo'], datos['periodo'])}",
            )
            self.limpiar_formulario()
            self.registro_guardado.emit()

        except Exception as e:
            logger.error("Error al guardar registro: %s", e, exc_info=True)
            QMessageBox.critical(
                self,
                "Error al guardar",
                f"No se pudo guardar el registro:\n{e}",
            )

    def limpiar_formulario(self) -> None:
        """Restablece todos los campos al estado inicial."""
        self._date_edit.setDate(QDate.currentDate())
        self._combo_periodo.setCurrentIndex(0)

        for spin in [
            self._spin_sistolica, self._spin_diastolica, self._spin_ritmo,
            self._spin_pasos, self._spin_calorias, self._spin_cafeina,
        ]:
            spin.setValue(spin.minimum())

        for spin in [
            self._spin_spo2, self._spin_peso, self._spin_distancia,
            self._spin_sueno, self._spin_glucosa, self._spin_temperatura, self._spin_agua,
        ]:
            spin.setValue(spin.minimum())

        self._slider_calidad_sueno.setValue(None)
        self._slider_estres.setValue(None)
        self._slider_animo.setValue(None)

        self._txt_medicamentos.clear()
        self._txt_sintomas.clear()
        self._txt_notas.clear()
        self._txt_ejercicio.clear()
        self._lbl_imc.setText("—")
