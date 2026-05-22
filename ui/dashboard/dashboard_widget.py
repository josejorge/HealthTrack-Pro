"""
Widget principal del Dashboard de HealthTrack Pro.

Muestra el resumen del día, tarjetas de métricas, alertas activas,
gráfica de tendencia y insights automáticos.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from charts.linea_temporal import GraficaPresionArterial, GraficaLineaTemporal
from services.alertas_service import ServicioAlertas
from services.estadisticas_service import ServicioEstadisticas
from services.insights_service import ServicioInsights, Insight
from services.registro_service import ServicioRegistro
from widgets.metric_card import TarjetaMetrica
from core.constants import (
    COLORES_CRITICIDAD,
    CRITICIDAD_NORMAL,
    PERIODOS,
)

logger = logging.getLogger("healthtrack.ui.dashboard")

DIAS_TENDENCIA = 14


class SeccionAlertas(QWidget):
    """Panel compacto que lista las alertas activas."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def actualizar(self, alertas: list) -> None:
        """Reemplaza el contenido con las alertas actuales."""
        # Limpiar
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not alertas:
            lbl = QLabel("✓  Sin alertas activas — todo en orden")
            lbl.setStyleSheet("color: #22c55e; font-size: 12px; padding: 8px;")
            self._layout.addWidget(lbl)
            return

        for alerta in alertas[:5]:
            fila = QFrame()
            fila.setObjectName(f"alerta_{alerta.criticidad}")
            fila_layout = QHBoxLayout(fila)
            fila_layout.setContentsMargins(12, 8, 12, 8)
            fila_layout.setSpacing(10)

            color = COLORES_CRITICIDAD.get(alerta.criticidad, "#94a3b8")
            iconos = {"normal": "✓", "atencion": "⚠", "preocupante": "⚠", "critico": "✕"}
            icono = iconos.get(alerta.criticidad, "•")

            lbl_icono = QLabel(icono)
            lbl_icono.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
            lbl_icono.setFixedWidth(20)

            lbl_texto = QLabel(f"<b>{alerta.titulo}</b>  {alerta.descripcion or ''}")
            lbl_texto.setWordWrap(True)
            lbl_texto.setStyleSheet("font-size: 11px;")

            lbl_fecha = QLabel(alerta.fecha.strftime("%d/%m") if alerta.fecha else "")
            lbl_fecha.setStyleSheet("color: #94a3b8; font-size: 10px;")
            lbl_fecha.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            fila_layout.addWidget(lbl_icono)
            fila_layout.addWidget(lbl_texto, 1)
            fila_layout.addWidget(lbl_fecha)

            self._layout.addWidget(fila)


class SeccionInsights(QWidget):
    """Panel de insights automáticos generados por el sistema."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def actualizar(self, insights: list[Insight]) -> None:
        """Reemplaza los insights actuales."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not insights:
            lbl = QLabel("Registra más datos para obtener insights")
            lbl.setStyleSheet("color: #94a3b8; font-size: 12px; padding: 4px;")
            self._layout.addWidget(lbl)
            return

        for insight in insights:
            fila = QFrame()
            fila_layout = QHBoxLayout(fila)
            fila_layout.setContentsMargins(0, 4, 0, 4)
            fila_layout.setSpacing(10)

            color_texto = "#22c55e" if insight.positivo else "#94a3b8"

            lbl_icono = QLabel(insight.icono)
            lbl_icono.setFixedWidth(24)
            lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl_texto = QLabel(insight.texto)
            lbl_texto.setWordWrap(True)
            lbl_texto.setStyleSheet(f"color: {color_texto}; font-size: 12px;")

            fila_layout.addWidget(lbl_icono)
            fila_layout.addWidget(lbl_texto, 1)

            self._layout.addWidget(fila)


class DashboardWidget(QWidget):
    """
    Panel principal de la aplicación.

    Estructura:
    ├── Encabezado (saludo + fecha + botón nuevo registro)
    ├── Tarjetas de métricas (4 en una fila)
    ├── Sección inferior
    │   ├── Izquierda: Gráfica de presión + gráfica pasos
    │   └── Derecha: Alertas activas + Insights
    """

    solicitar_nuevo_registro = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._servicio_registro = ServicioRegistro()
        self._servicio_estadisticas = ServicioEstadisticas()
        self._servicio_alertas = ServicioAlertas()
        self._servicio_insights = ServicioInsights()

        self._construir_ui()

        # Auto-actualizar cada 60 segundos
        self._timer = QTimer(self)
        self._timer.setInterval(60_000)
        self._timer.timeout.connect(self.actualizar_datos)
        self._timer.start()

        self.actualizar_datos()

    # ──────────────────────────────────────────
    # Construcción de la UI
    # ──────────────────────────────────────────

    def _construir_ui(self) -> None:
        """Construye todos los elementos visuales del dashboard."""
        # Widget scrollable principal
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        contenedor = QWidget()
        scroll.setWidget(contenedor)

        layout_principal = QVBoxLayout(contenedor)
        layout_principal.setContentsMargins(28, 24, 28, 28)
        layout_principal.setSpacing(20)

        # ── Encabezado ────────────────────────────
        layout_principal.addLayout(self._crear_encabezado())

        # ── Tarjetas de métricas ──────────────────
        layout_principal.addWidget(self._crear_seccion_tarjetas())

        # ── Sección inferior (gráficas + panel) ───
        layout_principal.addLayout(self._crear_seccion_inferior())

        layout_principal.addStretch()

        # Layout externo que contiene el scroll
        layout_externo = QVBoxLayout(self)
        layout_externo.setContentsMargins(0, 0, 0, 0)
        layout_externo.addWidget(scroll)

    def _crear_encabezado(self) -> QHBoxLayout:
        """Crea la fila de encabezado con saludo y botón de nuevo registro."""
        fila = QHBoxLayout()
        fila.setSpacing(16)

        # Bloque de saludo
        col_saludo = QVBoxLayout()
        col_saludo.setSpacing(2)

        self._lbl_saludo = QLabel()
        self._lbl_saludo.setObjectName("titulo_seccion")
        self._lbl_fecha = QLabel()
        self._lbl_fecha.setObjectName("subtitulo_seccion")

        col_saludo.addWidget(self._lbl_saludo)
        col_saludo.addWidget(self._lbl_fecha)

        fila.addLayout(col_saludo)
        fila.addStretch()

        # Botón nuevo registro
        btn_nuevo = QPushButton("✚  Nuevo Registro")
        btn_nuevo.setObjectName("btn_primario")
        btn_nuevo.setFixedHeight(42)
        btn_nuevo.setFixedWidth(180)
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo.clicked.connect(self.solicitar_nuevo_registro.emit)

        fila.addWidget(btn_nuevo)
        return fila

    def _crear_seccion_tarjetas(self) -> QWidget:
        """Crea la cuadrícula de 4 tarjetas de métricas principales."""
        contenedor = QWidget()
        grid = QGridLayout(contenedor)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)

        # 4 tarjetas en una fila
        self._tarjeta_presion = TarjetaMetrica("Presión Arterial", "mmHg")
        self._tarjeta_pulso = TarjetaMetrica("Ritmo Cardíaco", "bpm")
        self._tarjeta_peso = TarjetaMetrica("Peso", "kg")
        self._tarjeta_spo2 = TarjetaMetrica("Oxigenación", "%")

        grid.addWidget(self._tarjeta_presion, 0, 0)
        grid.addWidget(self._tarjeta_pulso, 0, 1)
        grid.addWidget(self._tarjeta_peso, 0, 2)
        grid.addWidget(self._tarjeta_spo2, 0, 3)

        # Segunda fila de tarjetas
        self._tarjeta_pasos = TarjetaMetrica("Pasos", "pasos")
        self._tarjeta_sueno = TarjetaMetrica("Sueño", "h")
        self._tarjeta_estres = TarjetaMetrica("Estrés", "/10")
        self._tarjeta_animo = TarjetaMetrica("Estado de Ánimo", "/10")

        grid.addWidget(self._tarjeta_pasos, 1, 0)
        grid.addWidget(self._tarjeta_sueno, 1, 1)
        grid.addWidget(self._tarjeta_estres, 1, 2)
        grid.addWidget(self._tarjeta_animo, 1, 3)

        return contenedor

    def _crear_seccion_inferior(self) -> QHBoxLayout:
        """Crea la sección inferior con gráficas y panel de alertas/insights."""
        fila = QHBoxLayout()
        fila.setSpacing(16)

        # ── Columna izquierda: gráficas ───────────
        col_izq = QVBoxLayout()
        col_izq.setSpacing(16)

        # Contenedor de la gráfica de presión
        self._grafica_presion = GraficaPresionArterial()
        self._grafica_presion.setObjectName("chart_container")
        self._grafica_presion.setMinimumHeight(200)

        lbl_g1 = QLabel("Tendencia — Presión Arterial (últimos 14 días)")
        lbl_g1.setObjectName("card_titulo")
        lbl_g1.setContentsMargins(0, 0, 0, 4)

        contenedor_g1 = QWidget()
        contenedor_g1.setObjectName("chart_container")
        lay_g1 = QVBoxLayout(contenedor_g1)
        lay_g1.setContentsMargins(14, 12, 14, 10)
        lay_g1.addWidget(lbl_g1)
        lay_g1.addWidget(self._grafica_presion)

        # Gráfica de pasos
        self._grafica_pasos = GraficaLineaTemporal(titulo="", unidad="pasos", alto_figura=2.5)
        lbl_g2 = QLabel("Pasos diarios (últimos 14 días)")
        lbl_g2.setObjectName("card_titulo")
        lbl_g2.setContentsMargins(0, 0, 0, 4)

        contenedor_g2 = QWidget()
        contenedor_g2.setObjectName("chart_container")
        lay_g2 = QVBoxLayout(contenedor_g2)
        lay_g2.setContentsMargins(14, 12, 14, 10)
        lay_g2.addWidget(lbl_g2)
        lay_g2.addWidget(self._grafica_pasos)

        col_izq.addWidget(contenedor_g1)
        col_izq.addWidget(contenedor_g2)

        # ── Columna derecha: alertas + insights ───
        col_der = QVBoxLayout()
        col_der.setSpacing(16)
        col_der.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Panel de alertas
        panel_alertas = self._crear_panel("🔔  Alertas Activas")
        self._seccion_alertas = SeccionAlertas()
        panel_alertas.layout().addWidget(self._seccion_alertas)

        # Panel de insights
        panel_insights = self._crear_panel("💡  Insights")
        self._seccion_insights = SeccionInsights()
        panel_insights.layout().addWidget(self._seccion_insights)

        col_der.addWidget(panel_alertas)
        col_der.addWidget(panel_insights)
        col_der.addStretch()

        fila.addLayout(col_izq, 3)
        fila.addLayout(col_der, 2)
        return fila

    def _crear_panel(self, titulo: str) -> QWidget:
        """Crea un panel con fondo de tarjeta y título."""
        panel = QWidget()
        panel.setObjectName("chart_container")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        lbl = QLabel(titulo)
        lbl.setObjectName("card_titulo")
        layout.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        return panel

    # ──────────────────────────────────────────
    # Actualización de datos
    # ──────────────────────────────────────────

    def actualizar_datos(self) -> None:
        """Carga todos los datos frescos y actualiza cada sección del dashboard."""
        try:
            self._actualizar_encabezado()
            self._actualizar_tarjetas()
            self._actualizar_graficas()
            self._actualizar_alertas()
            self._actualizar_insights()
        except Exception as e:
            logger.error("Error al actualizar el dashboard: %s", e, exc_info=True)

    def _actualizar_encabezado(self) -> None:
        """Actualiza el saludo y la fecha."""
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos días"
        elif hora < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"

        from core.config import config
        nombre = config.usuario_nombre
        self._lbl_saludo.setText(f"{saludo}, {nombre} 👋")

        hoy = date.today()
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        dia_nombre = dias_semana[hoy.weekday()]
        mes_nombre = meses[hoy.month - 1]
        self._lbl_fecha.setText(f"{dia_nombre}, {hoy.day} de {mes_nombre} de {hoy.year}")

    def _actualizar_tarjetas(self) -> None:
        """Actualiza las tarjetas de métricas con los datos más recientes."""
        resumen = self._servicio_estadisticas.resumen_hoy()

        if not resumen.get("tiene_datos"):
            # Estado vacío
            for tarjeta in [
                self._tarjeta_presion, self._tarjeta_pulso,
                self._tarjeta_peso, self._tarjeta_spo2,
                self._tarjeta_pasos, self._tarjeta_sueno,
                self._tarjeta_estres, self._tarjeta_animo,
            ]:
                tarjeta.limpiar()
            return

        # Obtener resúmenes de estadísticas para tendencias
        res_sis = self._servicio_estadisticas.calcular_resumen("presion_sistolica", 14)
        res_pulso = self._servicio_estadisticas.calcular_resumen("ritmo_cardiaco", 14)
        res_peso = self._servicio_estadisticas.calcular_resumen("peso", 14)
        res_spo2 = self._servicio_estadisticas.calcular_resumen("oxigenacion", 14)
        res_pasos = self._servicio_estadisticas.calcular_resumen("pasos", 14)
        res_sueno = self._servicio_estadisticas.calcular_resumen("horas_sueno", 14)
        res_estres = self._servicio_estadisticas.calcular_resumen("nivel_estres", 14)
        res_animo = self._servicio_estadisticas.calcular_resumen("estado_animo", 14)

        # Presión arterial
        sis = resumen.get("presion_sistolica")
        dia = resumen.get("presion_diastolica")
        if sis and dia:
            self._tarjeta_presion.actualizar(
                valor=f"{sis:.0f}/{dia:.0f}",
                criticidad=self._criticidad_presion(sis, dia),
                tendencia=res_sis.tendencia if res_sis else "estable",
                tendencia_pct=res_sis.tendencia_porcentaje if res_sis else 0,
            )

        # Ritmo cardíaco
        pulso = resumen.get("ritmo_cardiaco")
        if pulso:
            self._tarjeta_pulso.actualizar(
                valor=f"{pulso:.0f}",
                criticidad=self._criticidad_pulso(pulso),
                tendencia=res_pulso.tendencia if res_pulso else "estable",
                tendencia_pct=res_pulso.tendencia_porcentaje if res_pulso else 0,
            )

        # Peso
        peso = resumen.get("peso")
        if peso:
            self._tarjeta_peso.actualizar(
                valor=f"{peso:.1f}",
                criticidad=CRITICIDAD_NORMAL,
                tendencia=res_peso.tendencia if res_peso else "estable",
                tendencia_pct=res_peso.tendencia_porcentaje if res_peso else 0,
            )

        # SpO2
        spo2 = resumen.get("oxigenacion")
        if spo2:
            self._tarjeta_spo2.actualizar(
                valor=f"{spo2:.0f}",
                criticidad=self._criticidad_spo2(spo2),
                tendencia=res_spo2.tendencia if res_spo2 else "estable",
                tendencia_pct=res_spo2.tendencia_porcentaje if res_spo2 else 0,
            )

        # Pasos
        pasos = resumen.get("pasos")
        if pasos:
            from core.config import config
            objetivo = config.usuario_pasos_objetivo
            pct = min(100, (pasos / objetivo) * 100) if objetivo else 0
            self._tarjeta_pasos.actualizar(
                valor=f"{int(pasos):,}",
                criticidad=CRITICIDAD_NORMAL if pct >= 70 else "atencion",
                tendencia=res_pasos.tendencia if res_pasos else "estable",
                tendencia_pct=res_pasos.tendencia_porcentaje if res_pasos else 0,
                subtexto=f"{pct:.0f}% del objetivo",
            )

        # Sueño
        sueno = resumen.get("horas_sueno")
        if sueno:
            from core.constants import SUENO, CRITICIDAD_ATENCION
            crit_sueno = CRITICIDAD_ATENCION if sueno < SUENO["recomendado_min"] else CRITICIDAD_NORMAL
            self._tarjeta_sueno.actualizar(
                valor=f"{sueno:.1f}",
                criticidad=crit_sueno,
                tendencia=res_sueno.tendencia if res_sueno else "estable",
                tendencia_pct=res_sueno.tendencia_porcentaje if res_sueno else 0,
            )

        # Estrés
        estres = resumen.get("nivel_estres")
        if estres:
            from core.constants import ESCALA_ESTRES, CRITICIDAD_PREOCUPANTE, CRITICIDAD_ATENCION
            if estres >= ESCALA_ESTRES["muy_alto_min"]:
                crit_estres = CRITICIDAD_PREOCUPANTE
            elif estres >= ESCALA_ESTRES["alto_min"]:
                crit_estres = CRITICIDAD_ATENCION
            else:
                crit_estres = CRITICIDAD_NORMAL
            self._tarjeta_estres.actualizar(
                valor=f"{estres:.0f}",
                criticidad=crit_estres,
                tendencia=res_estres.tendencia if res_estres else "estable",
                tendencia_pct=res_estres.tendencia_porcentaje if res_estres else 0,
            )

        # Ánimo
        animo = resumen.get("estado_animo")
        if animo:
            from core.constants import ESCALA_ANIMO
            crit_animo = CRITICIDAD_NORMAL if animo >= ESCALA_ANIMO["normal_min"] else "atencion"
            self._tarjeta_animo.actualizar(
                valor=f"{animo:.0f}",
                criticidad=crit_animo,
                tendencia=res_animo.tendencia if res_animo else "estable",
                tendencia_pct=res_animo.tendencia_porcentaje if res_animo else 0,
            )

    def _actualizar_graficas(self) -> None:
        """Carga datos en las gráficas de tendencia."""
        try:
            fechas_s, vals_s = self._servicio_estadisticas.serie_temporal(
                "presion_sistolica", DIAS_TENDENCIA
            )
            fechas_d, vals_d = self._servicio_estadisticas.serie_temporal(
                "presion_diastolica", DIAS_TENDENCIA
            )
            self._grafica_presion.cargar_datos(fechas_s, vals_s, fechas_d, vals_d)

            fechas_p, vals_p = self._servicio_estadisticas.serie_temporal(
                "pasos", DIAS_TENDENCIA
            )
            self._grafica_pasos.limpiar_series()
            self._grafica_pasos.agregar_serie(fechas_p, vals_p, "Pasos", "#6366f1")
            self._grafica_pasos.dibujar()
        except Exception as e:
            logger.warning("No se pudieron cargar las gráficas: %s", e)

    def _actualizar_alertas(self) -> None:
        """Actualiza el panel de alertas."""
        alertas = self._servicio_alertas.obtener_alertas_activas()
        self._seccion_alertas.actualizar(alertas)

    def _actualizar_insights(self) -> None:
        """Actualiza el panel de insights."""
        insights = self._servicio_insights.generar_insights(30)
        self._seccion_insights.actualizar(insights)

    # ──────────────────────────────────────────
    # Helpers de criticidad
    # ──────────────────────────────────────────

    @staticmethod
    def _criticidad_presion(sistolica: float, diastolica: float) -> str:
        from core.constants import (
            CRITICIDAD_CRITICO, CRITICIDAD_PREOCUPANTE,
            CRITICIDAD_ATENCION, CRITICIDAD_NORMAL,
            PRESION_SISTOLICA, PRESION_DIASTOLICA,
        )
        if sistolica >= PRESION_SISTOLICA["crisis_min"] or diastolica >= PRESION_DIASTOLICA["crisis_min"]:
            return CRITICIDAD_CRITICO
        if sistolica >= PRESION_SISTOLICA["alta_2_min"] or diastolica >= PRESION_DIASTOLICA["alta_2_min"]:
            return CRITICIDAD_PREOCUPANTE
        if sistolica >= PRESION_SISTOLICA["alta_1_min"] or diastolica >= PRESION_DIASTOLICA["alta_1_min"]:
            return CRITICIDAD_ATENCION
        return CRITICIDAD_NORMAL

    @staticmethod
    def _criticidad_pulso(pulso: float) -> str:
        from core.constants import CRITICIDAD_CRITICO, CRITICIDAD_ATENCION, CRITICIDAD_NORMAL, RITMO_CARDIACO
        if pulso >= RITMO_CARDIACO["critico_min"] or pulso < 40:
            return CRITICIDAD_CRITICO
        if pulso >= RITMO_CARDIACO["taquicardia_min"] or pulso < RITMO_CARDIACO["bradicardia_max"]:
            return CRITICIDAD_ATENCION
        return CRITICIDAD_NORMAL

    @staticmethod
    def _criticidad_spo2(spo2: float) -> str:
        from core.constants import CRITICIDAD_CRITICO, CRITICIDAD_PREOCUPANTE, CRITICIDAD_ATENCION, CRITICIDAD_NORMAL, OXIGENACION
        if spo2 < OXIGENACION["baja_min"]:
            return CRITICIDAD_CRITICO
        if spo2 < OXIGENACION["normal_min"]:
            return CRITICIDAD_ATENCION
        return CRITICIDAD_NORMAL
