"""
Widget de historial de registros de salud.

Muestra un calendario interactivo donde los días con datos
están resaltados, y una tabla con los registros del día seleccionado.
"""

from __future__ import annotations

import logging
from datetime import date

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from services.registro_service import ServicioRegistro
from services.exportacion_service import ServicioExportacion
from core.constants import (
    COLORES_CRITICIDAD,
    CRITICIDAD_NORMAL,
    PERIODOS,
)

logger = logging.getLogger("healthtrack.ui.historial")


def _celda(texto: str, alineacion: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter) -> QTableWidgetItem:
    """Crea una celda de tabla de solo lectura."""
    item = QTableWidgetItem(str(texto))
    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    item.setTextAlignment(alineacion)
    return item


class HistorialWidget(QWidget):
    """
    Vista de historial con calendario interactivo y tabla de registros.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._servicio = ServicioRegistro()
        self._servicio_export = ServicioExportacion()
        self._fecha_seleccionada: date = date.today()
        self._fechas_con_datos: set[date] = set()

        self._construir_ui()
        self._cargar_fechas_con_datos()
        self._cargar_registros_fecha(self._fecha_seleccionada)

    # ──────────────────────────────────────────
    # Construcción de UI
    # ──────────────────────────────────────────

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(28, 24, 28, 28)
        layout_principal.setSpacing(16)

        # ── Encabezado ────────────────────────────
        fila_header = QHBoxLayout()
        titulo = QLabel("Historial de Registros")
        titulo.setObjectName("titulo_seccion")
        fila_header.addWidget(titulo)
        fila_header.addStretch()

        btn_exportar = QPushButton("↗  Exportar")
        btn_exportar.setObjectName("btn_secundario")
        btn_exportar.setFixedHeight(38)
        btn_exportar.clicked.connect(self._exportar)
        fila_header.addWidget(btn_exportar)
        layout_principal.addLayout(fila_header)

        # ── Cuerpo: Calendario + Tabla ────────────
        fila_cuerpo = QHBoxLayout()
        fila_cuerpo.setSpacing(20)

        # Columna calendario
        col_izq = QVBoxLayout()
        col_izq.setSpacing(10)
        col_izq.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_cal = QLabel("Selecciona un día")
        lbl_cal.setObjectName("etiqueta_campo")
        col_izq.addWidget(lbl_cal)

        self._calendario = QCalendarWidget()
        self._calendario.setGridVisible(True)
        self._calendario.setNavigationBarVisible(True)
        self._calendario.setMaximumDate(QDate.currentDate())
        self._calendario.setFixedWidth(340)
        self._calendario.selectionChanged.connect(self._on_fecha_seleccionada)
        col_izq.addWidget(self._calendario)

        # Leyenda del calendario
        leyenda = QHBoxLayout()
        for color, texto in [("#6366f1", "Con datos"), ("#ef4444", "Alerta crítica")]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            lbl = QLabel(texto)
            lbl.setObjectName("etiqueta_campo")
            leyenda.addWidget(dot)
            leyenda.addWidget(lbl)
            leyenda.addSpacing(12)
        leyenda.addStretch()
        col_izq.addLayout(leyenda)

        # Resumen del día seleccionado
        self._panel_resumen = self._crear_panel_resumen()
        col_izq.addWidget(self._panel_resumen)

        fila_cuerpo.addLayout(col_izq)

        # Columna tabla
        col_der = QVBoxLayout()
        col_der.setSpacing(10)

        self._lbl_titulo_tabla = QLabel("Registros del día")
        self._lbl_titulo_tabla.setObjectName("etiqueta_campo")
        col_der.addWidget(self._lbl_titulo_tabla)

        self._tabla = self._crear_tabla()
        col_der.addWidget(self._tabla, 1)

        # Botón eliminar
        fila_acciones = QHBoxLayout()
        fila_acciones.addStretch()
        self._btn_eliminar = QPushButton("🗑  Eliminar Registro Seleccionado")
        self._btn_eliminar.setObjectName("btn_peligro")
        self._btn_eliminar.setFixedHeight(36)
        self._btn_eliminar.clicked.connect(self._eliminar_seleccionado)
        fila_acciones.addWidget(self._btn_eliminar)
        col_der.addLayout(fila_acciones)

        fila_cuerpo.addLayout(col_der, 1)
        layout_principal.addLayout(fila_cuerpo)

    def _crear_panel_resumen(self) -> QWidget:
        """Panel con métricas rápidas del día seleccionado."""
        panel = QWidget()
        panel.setObjectName("chart_container")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        lbl = QLabel("Resumen del día")
        lbl.setObjectName("card_titulo")
        layout.addWidget(lbl)

        self._lbl_resumen_contenido = QLabel("Selecciona un día para ver el resumen")
        self._lbl_resumen_contenido.setWordWrap(True)
        self._lbl_resumen_contenido.setObjectName("subtitulo_seccion")
        layout.addWidget(self._lbl_resumen_contenido)

        return panel

    def _crear_tabla(self) -> QTableWidget:
        """Tabla de registros del día seleccionado."""
        columnas = [
            "Período", "P. Sistólica", "P. Diastólica", "Ritmo Cardíaco",
            "SpO2 %", "Peso kg", "Pasos", "Sueño h",
            "Estrés", "Ánimo", "Criticidad",
        ]
        tabla = QTableWidget(0, len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.setAlternatingRowColors(True)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.verticalHeader().setVisible(False)
        tabla.setShowGrid(False)
        return tabla

    # ──────────────────────────────────────────
    # Datos
    # ──────────────────────────────────────────

    def _cargar_fechas_con_datos(self) -> None:
        """Obtiene todas las fechas que tienen registros y los resalta en el calendario."""
        fechas = self._servicio.fechas_con_registros()
        self._fechas_con_datos = set(fechas)
        self._resaltar_calendario(fechas)

    def _resaltar_calendario(self, fechas: list[date]) -> None:
        """Aplica formato especial a los días con datos en el calendario."""
        fmt_con_datos = QTextCharFormat()
        fmt_con_datos.setBackground(QBrush(QColor("#6366f1")))
        fmt_con_datos.setForeground(QBrush(QColor("#ffffff")))
        fuente_bold = QFont()
        fuente_bold.setBold(True)
        fmt_con_datos.setFont(fuente_bold)

        for f in fechas:
            qdate = QDate(f.year, f.month, f.day)
            self._calendario.setDateTextFormat(qdate, fmt_con_datos)

    def _on_fecha_seleccionada(self) -> None:
        """Callback cuando el usuario selecciona un día en el calendario."""
        qdate = self._calendario.selectedDate()
        self._fecha_seleccionada = date(qdate.year(), qdate.month(), qdate.day())
        self._cargar_registros_fecha(self._fecha_seleccionada)

    def _cargar_registros_fecha(self, fecha: date) -> None:
        """Carga y muestra los registros de la fecha seleccionada en la tabla."""
        registros = self._servicio.obtener_por_fecha(fecha)

        fecha_str = fecha.strftime("%A, %d de %B de %Y").capitalize()
        self._lbl_titulo_tabla.setText(
            f"Registros del {fecha.strftime('%d/%m/%Y')} ({len(registros)} registros)"
        )

        self._tabla.setRowCount(0)
        self._tabla.setRowCount(len(registros))

        for fila_idx, reg in enumerate(registros):
            criticidad = reg.criticidad_general()
            color_hex = COLORES_CRITICIDAD.get(criticidad, "#94a3b8")

            valores = [
                PERIODOS.get(reg.periodo, reg.periodo),
                f"{reg.presion_sistolica}" if reg.presion_sistolica else "—",
                f"{reg.presion_diastolica}" if reg.presion_diastolica else "—",
                f"{reg.ritmo_cardiaco}" if reg.ritmo_cardiaco else "—",
                f"{reg.oxigenacion}" if reg.oxigenacion else "—",
                f"{reg.peso:.1f}" if reg.peso else "—",
                f"{reg.pasos:,}" if reg.pasos else "—",
                f"{reg.horas_sueno:.1f}" if reg.horas_sueno else "—",
                f"{reg.nivel_estres}" if reg.nivel_estres else "—",
                f"{reg.estado_animo}" if reg.estado_animo else "—",
                criticidad.capitalize(),
            ]

            for col_idx, valor in enumerate(valores):
                item = _celda(valor)
                # Colorear la celda de criticidad
                if col_idx == len(valores) - 1:
                    item.setForeground(QBrush(QColor(color_hex)))
                    fuente = QFont()
                    fuente.setBold(True)
                    item.setFont(fuente)
                # Guardar el ID del registro en la columna oculta
                item.setData(Qt.ItemDataRole.UserRole, reg.id)
                self._tabla.setItem(fila_idx, col_idx, item)

        # Actualizar resumen
        self._actualizar_resumen(registros)

    def _actualizar_resumen(self, registros) -> None:
        """Actualiza el panel de resumen con datos del día."""
        if not registros:
            self._lbl_resumen_contenido.setText("Sin registros para este día")
            return

        lineas = []
        for reg in registros:
            periodo = PERIODOS.get(reg.periodo, reg.periodo)
            lineas.append(f"<b>{periodo}:</b>")
            if reg.presion_sistolica:
                lineas.append(f"  PA: {reg.presion_sistolica}/{reg.presion_diastolica} mmHg")
            if reg.ritmo_cardiaco:
                lineas.append(f"  FC: {reg.ritmo_cardiaco} bpm")
            if reg.peso:
                lineas.append(f"  Peso: {reg.peso:.1f} kg")
        self._lbl_resumen_contenido.setText("<br>".join(lineas))

    def _eliminar_seleccionado(self) -> None:
        """Elimina el registro seleccionado en la tabla."""
        fila = self._tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Sin selección", "Selecciona un registro para eliminar.")
            return

        item = self._tabla.item(fila, 0)
        if item is None:
            return
        id_registro = item.data(Qt.ItemDataRole.UserRole)

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar este registro? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            if self._servicio.eliminar_registro(id_registro):
                self._cargar_registros_fecha(self._fecha_seleccionada)
                self._cargar_fechas_con_datos()
                QMessageBox.information(self, "Eliminado", "Registro eliminado correctamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el registro.")

    def _exportar(self) -> None:
        """Exporta los datos del historial a CSV."""
        try:
            ruta = self._servicio_export.exportar_csv()
            QMessageBox.information(
                self, "Exportación completada",
                f"Datos exportados correctamente:\n{ruta}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error de exportación", str(e))

    def actualizar(self) -> None:
        """Refresca el historial (llamar después de guardar un nuevo registro)."""
        self._cargar_fechas_con_datos()
        self._cargar_registros_fecha(self._fecha_seleccionada)
