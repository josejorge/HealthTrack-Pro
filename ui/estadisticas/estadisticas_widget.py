"""
Widget de estadísticas y análisis de datos de salud.

Muestra gráficas interactivas, resúmenes estadísticos, récords
históricos y comparativas de períodos para todas las métricas.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from charts.linea_temporal import GraficaLineaTemporal
from charts.barras import GraficaBarras
from services.estadisticas_service import ServicioEstadisticas, ResumenEstadistico
from services.exportacion_service import ServicioExportacion
from core.constants import GRAFICA_PERIODOS_DISPLAY, GRAFICA_COLORES_SERIES

logger = logging.getLogger("healthtrack.ui.estadisticas")


def _card_estadistica(titulo: str, valor: str, subtexto: str = "") -> QWidget:
    """Mini tarjeta para mostrar un único valor estadístico."""
    frame = QFrame()
    frame.setObjectName("metric_card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 10, 14, 10)
    layout.setSpacing(2)

    lbl_titulo = QLabel(titulo.upper())
    lbl_titulo.setObjectName("card_titulo")

    lbl_valor = QLabel(str(valor))
    lbl_valor.setStyleSheet("font-size: 22px; font-weight: 700;")

    layout.addWidget(lbl_titulo)
    layout.addWidget(lbl_valor)

    if subtexto:
        lbl_sub = QLabel(subtexto)
        lbl_sub.setObjectName("subtitulo_seccion")
        layout.addWidget(lbl_sub)

    return frame


class PanelMetrica(QWidget):
    """
    Panel de análisis completo para una métrica individual.

    Muestra: gráfica de tendencia, mini-cards estadísticas,
    y comparativa semanas anteriores.
    """

    def __init__(
        self,
        metrica: str,
        etiqueta: str,
        unidad: str,
        color: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._metrica = metrica
        self._etiqueta = etiqueta
        self._unidad = unidad
        self._color = color
        self._servicio = ServicioEstadisticas()
        self._dias = 30

        self._construir_ui()
        self.actualizar(30)

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Cards de estadísticas
        self._grid_cards = QGridLayout()
        self._grid_cards.setSpacing(10)
        layout.addLayout(self._grid_cards)

        # Gráfica de tendencia
        contenedor_grafica = QWidget()
        contenedor_grafica.setObjectName("chart_container")
        lay_g = QVBoxLayout(contenedor_grafica)
        lay_g.setContentsMargins(14, 12, 14, 10)

        self._grafica = GraficaLineaTemporal(
            titulo=f"Tendencia — {self._etiqueta}",
            unidad=self._unidad,
            alto_figura=3.2,
        )
        lay_g.addWidget(self._grafica)
        layout.addWidget(contenedor_grafica)

        # Gráfica de promedios semanales
        contenedor_barras = QWidget()
        contenedor_barras.setObjectName("chart_container")
        lay_b = QVBoxLayout(contenedor_barras)
        lay_b.setContentsMargins(14, 12, 14, 10)
        lbl_barras = QLabel(f"Promedios semanales — {self._etiqueta}")
        lbl_barras.setObjectName("card_titulo")
        lay_b.addWidget(lbl_barras)
        self._grafica_barras = GraficaBarras(unidad=self._unidad, alto_figura=2.4)
        lay_b.addWidget(self._grafica_barras)
        layout.addWidget(contenedor_barras)

    def actualizar(self, dias: int) -> None:
        """Actualiza toda la sección con el nuevo período."""
        self._dias = dias
        resumen = self._servicio.calcular_resumen(self._metrica, dias)

        # Limpiar y reconstruir cards
        while self._grid_cards.count():
            item = self._grid_cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if resumen and resumen.total_registros > 0:
            cards = [
                ("Promedio", f"{resumen.promedio or 0:.1f}", self._unidad),
                ("Mediana", f"{resumen.mediana or 0:.1f}", self._unidad),
                ("Máximo", f"{resumen.maximo or 0:.1f}", f"{resumen.fecha_maximo or ''}"),
                ("Mínimo", f"{resumen.minimo or 0:.1f}", f"{resumen.fecha_minimo or ''}"),
                ("Desv. Est.", f"{resumen.desviacion_std or 0:.2f}", ""),
                ("Registros", f"{resumen.total_registros}", f"en {dias} días"),
            ]
        else:
            cards = [("Sin datos", "—", f"Últimos {dias} días")]

        for i, (titulo, valor, sub) in enumerate(cards):
            card = _card_estadistica(titulo, valor, sub)
            self._grid_cards.addWidget(card, i // 3, i % 3)

        # Actualizar gráfica de tendencia
        fechas, valores = self._servicio.serie_temporal(self._metrica, dias)
        self._grafica.limpiar_series()
        self._grafica.agregar_serie(fechas, valores, self._etiqueta, self._color)
        self._grafica.dibujar()

        # Gráfica de promedios semanales
        self._actualizar_promedios_semanales(dias)

    def _actualizar_promedios_semanales(self, dias: int) -> None:
        """Calcula y muestra promedios semanales en la gráfica de barras."""
        fechas, valores = self._servicio.serie_temporal(self._metrica, dias)
        if not fechas or not valores:
            return

        # Agrupar en semanas
        semanas: dict[int, list[float]] = {}
        for f, v in zip(fechas, valores):
            semana = f.isocalendar()[1]  # número de semana del año
            semanas.setdefault(semana, []).append(v)

        import statistics
        categorias = [f"Sem. {s}" for s in sorted(semanas.keys())]
        promedios = [
            round(statistics.mean(semanas[s]), 1)
            for s in sorted(semanas.keys())
        ]

        self._grafica_barras.cargar_datos(categorias, promedios)


class EstadisticasWidget(QWidget):
    """
    Panel principal de estadísticas con tabs por categoría.

    Tabs:
    - Cardiovascular (presión, pulso, SpO2)
    - Física (peso, IMC, pasos)
    - Descanso & Mental (sueño, estrés, ánimo)
    - Récords históricos
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._servicio = ServicioEstadisticas()
        self._servicio_export = ServicioExportacion()
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        # ── Encabezado ────────────────────────────
        fila_header = QHBoxLayout()
        titulo = QLabel("Estadísticas y Análisis")
        titulo.setObjectName("titulo_seccion")
        fila_header.addWidget(titulo)
        fila_header.addStretch()

        # Selector de período
        lbl_periodo = QLabel("Período:")
        lbl_periodo.setObjectName("etiqueta_campo")
        self._combo_periodo = QComboBox()
        for clave, etiqueta in GRAFICA_PERIODOS_DISPLAY.items():
            self._combo_periodo.addItem(etiqueta, clave)
        self._combo_periodo.setCurrentIndex(1)  # 30 días por defecto
        self._combo_periodo.currentIndexChanged.connect(self._on_periodo_cambiado)
        self._combo_periodo.setFixedWidth(180)

        btn_exportar_pdf = QPushButton("PDF")
        btn_exportar_pdf.setObjectName("btn_secundario")
        btn_exportar_pdf.setFixedHeight(36)
        btn_exportar_pdf.setFixedWidth(70)
        btn_exportar_pdf.clicked.connect(lambda: self._exportar("pdf"))

        btn_exportar_excel = QPushButton("Excel")
        btn_exportar_excel.setObjectName("btn_secundario")
        btn_exportar_excel.setFixedHeight(36)
        btn_exportar_excel.setFixedWidth(80)
        btn_exportar_excel.clicked.connect(lambda: self._exportar("excel"))

        fila_header.addWidget(lbl_periodo)
        fila_header.addWidget(self._combo_periodo)
        fila_header.addWidget(btn_exportar_pdf)
        fila_header.addWidget(btn_exportar_excel)
        layout.addLayout(fila_header)

        # ── Tabs de categorías ────────────────────
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._tab_cardiovascular = self._crear_tab_cardiovascular()
        self._tab_fisica = self._crear_tab_fisica()
        self._tab_mental = self._crear_tab_mental()
        self._tab_records = self._crear_tab_records()

        self._tabs.addTab(self._tab_cardiovascular, "❤️  Cardiovascular")
        self._tabs.addTab(self._tab_fisica, "🏋️  Física")
        self._tabs.addTab(self._tab_mental, "🧠  Mental & Descanso")
        self._tabs.addTab(self._tab_records, "🏆  Récords")

        layout.addWidget(self._tabs)

    def _scroll_tab(self, widget: QWidget) -> QScrollArea:
        """Envuelve un widget en un área scrollable."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(widget)
        return scroll

    def _crear_tab_cardiovascular(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(16)

        self._panel_presion_s = PanelMetrica(
            "presion_sistolica", "Presión Sistólica", "mmHg", "#ef4444"
        )
        self._panel_presion_d = PanelMetrica(
            "presion_diastolica", "Presión Diastólica", "mmHg", "#6366f1"
        )
        self._panel_ritmo = PanelMetrica(
            "ritmo_cardiaco", "Ritmo Cardíaco", "bpm", "#f59e0b"
        )
        self._panel_spo2 = PanelMetrica(
            "oxigenacion", "Oxigenación SpO2", "%", "#22c55e"
        )

        layout.addWidget(self._panel_presion_s)
        layout.addWidget(self._panel_presion_d)
        layout.addWidget(self._panel_ritmo)
        layout.addWidget(self._panel_spo2)

        return self._scroll_tab(contenedor)

    def _crear_tab_fisica(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(16)

        self._panel_peso = PanelMetrica("peso", "Peso", "kg", "#6366f1")
        self._panel_imc = PanelMetrica("imc", "IMC", "kg/m²", "#f59e0b")
        self._panel_pasos = PanelMetrica("pasos", "Pasos", "pasos", "#22c55e")
        self._panel_calorias = PanelMetrica("calorias_quemadas", "Calorías Quemadas", "kcal", "#ef4444")

        layout.addWidget(self._panel_peso)
        layout.addWidget(self._panel_imc)
        layout.addWidget(self._panel_pasos)
        layout.addWidget(self._panel_calorias)

        return self._scroll_tab(contenedor)

    def _crear_tab_mental(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(16)

        self._panel_sueno = PanelMetrica("horas_sueno", "Horas de Sueño", "h", "#6366f1")
        self._panel_calidad_sueno = PanelMetrica("calidad_sueno", "Calidad del Sueño", "/10", "#22c55e")
        self._panel_estres = PanelMetrica("nivel_estres", "Nivel de Estrés", "/10", "#ef4444")
        self._panel_animo = PanelMetrica("estado_animo", "Estado de Ánimo", "/10", "#f59e0b")

        layout.addWidget(self._panel_sueno)
        layout.addWidget(self._panel_calidad_sueno)
        layout.addWidget(self._panel_estres)
        layout.addWidget(self._panel_animo)

        return self._scroll_tab(contenedor)

    def _crear_tab_records(self) -> QWidget:
        """Tab de récords históricos de todas las métricas."""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        lbl_titulo = QLabel("Récords Históricos Personales")
        lbl_titulo.setObjectName("titulo_seccion")
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel(
            "Máximos y mínimos registrados desde el inicio del seguimiento."
        )
        lbl_sub.setObjectName("subtitulo_seccion")
        layout.addWidget(lbl_sub)

        self._contenedor_records = QWidget()
        self._grid_records = QGridLayout(self._contenedor_records)
        self._grid_records.setSpacing(12)
        layout.addWidget(self._contenedor_records)
        layout.addStretch()

        self._actualizar_records()
        return self._scroll_tab(contenedor)

    def _actualizar_records(self) -> None:
        """Carga y muestra los récords históricos."""
        while self._grid_records.count():
            item = self._grid_records.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        records = self._servicio.obtener_records_historicos()

        if not records:
            lbl = QLabel("Aún no hay suficientes datos para mostrar récords.")
            lbl.setObjectName("subtitulo_seccion")
            self._grid_records.addWidget(lbl, 0, 0)
            return

        for i, record in enumerate(records):
            tipo_icono = "▲" if record.tipo == "maximo" else "▼"
            tipo_color = "#ef4444" if record.tipo == "maximo" else "#22c55e"
            fecha_str = record.fecha.strftime("%d/%m/%Y") if record.fecha else "—"

            card = QFrame()
            card.setObjectName("metric_card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)
            card_layout.setSpacing(4)

            lbl_tipo = QLabel(f"{tipo_icono} {record.tipo.upper()}")
            lbl_tipo.setStyleSheet(f"color: {tipo_color}; font-size: 10px; font-weight: bold;")
            card_layout.addWidget(lbl_tipo)

            lbl_nombre = QLabel(record.etiqueta)
            lbl_nombre.setObjectName("card_titulo")
            card_layout.addWidget(lbl_nombre)

            lbl_valor = QLabel(f"{record.valor:.1f} {record.unidad}")
            lbl_valor.setStyleSheet("font-size: 20px; font-weight: bold;")
            card_layout.addWidget(lbl_valor)

            lbl_fecha = QLabel(f"{fecha_str}  {record.periodo}")
            lbl_fecha.setObjectName("subtitulo_seccion")
            card_layout.addWidget(lbl_fecha)

            self._grid_records.addWidget(card, i // 4, i % 4)

    # ──────────────────────────────────────────
    # Eventos
    # ──────────────────────────────────────────

    def _on_periodo_cambiado(self) -> None:
        """Actualiza todas las gráficas al cambiar el período."""
        clave = self._combo_periodo.currentData()
        mapa_dias = {
            "7d": 7, "30d": 30, "90d": 90,
            "180d": 180, "365d": 365, "todo": 3650,
        }
        dias = mapa_dias.get(clave, 30)

        for panel in [
            self._panel_presion_s, self._panel_presion_d,
            self._panel_ritmo, self._panel_spo2,
            self._panel_peso, self._panel_imc,
            self._panel_pasos, self._panel_calorias,
            self._panel_sueno, self._panel_calidad_sueno,
            self._panel_estres, self._panel_animo,
        ]:
            try:
                panel.actualizar(dias)
            except Exception as e:
                logger.warning("Error actualizando panel: %s", e)

        self._actualizar_records()

    def _exportar(self, formato: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        try:
            if formato == "pdf":
                ruta = self._servicio_export.exportar_pdf()
            else:
                ruta = self._servicio_export.exportar_excel()

            QMessageBox.information(
                self, "Exportación completada",
                f"Archivo generado en:\n{ruta}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error de exportación", str(e))

    def actualizar(self) -> None:
        """Refresca todas las secciones."""
        self._on_periodo_cambiado()
