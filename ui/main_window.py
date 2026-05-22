"""
Ventana principal de HealthTrack Pro.

Ensambla el sidebar de navegación con el área de contenido
(QStackedWidget) y conecta todas las señales entre módulos.
"""

from __future__ import annotations

import logging
from datetime import date

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QFont, QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from widgets.sidebar import Sidebar
from widgets.theme_manager import gestor_tema
from ui.dashboard.dashboard_widget import DashboardWidget
from ui.registro.registro_widget import RegistroWidget
from ui.historial.historial_widget import HistorialWidget
from ui.estadisticas.estadisticas_widget import EstadisticasWidget
from ui.configuracion.configuracion_widget import ConfiguracionWidget
from services.alertas_service import ServicioAlertas
from core.constants import APP_NOMBRE, APP_VERSION, VENTANA_ANCHO_DEFAULT, VENTANA_ALTO_DEFAULT, VENTANA_ANCHO_MIN, VENTANA_ALTO_MIN

logger = logging.getLogger("healthtrack.ui.main_window")


class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de la aplicación.

    Estructura:
    ┌──────────────────────────────────────────────┐
    │  Sidebar  │        Contenido (tabs)           │
    │           │  Dashboard / Registro / ...       │
    └──────────────────────────────────────────────┘
    │  Barra de estado                              │
    └──────────────────────────────────────────────┘
    """

    def __init__(self) -> None:
        super().__init__()
        self._servicio_alertas = ServicioAlertas()
        self._modulo_actual = "dashboard"

        self._configurar_ventana()
        self._construir_ui()
        self._conectar_senales()
        self._iniciar_actualizacion_periodica()

        logger.info("Ventana principal inicializada")

    # ──────────────────────────────────────────
    # Configuración de la ventana
    # ──────────────────────────────────────────

    def _configurar_ventana(self) -> None:
        """Establece propiedades de la ventana."""
        self.setWindowTitle(f"{APP_NOMBRE} v{APP_VERSION}")
        self.setMinimumSize(VENTANA_ANCHO_MIN, VENTANA_ALTO_MIN)
        self.resize(VENTANA_ANCHO_DEFAULT, VENTANA_ALTO_DEFAULT)

        # Centrar en pantalla
        from PySide6.QtGui import QScreen
        from PySide6.QtWidgets import QApplication
        pantalla = QApplication.primaryScreen()
        if pantalla:
            geometria = pantalla.availableGeometry()
            self.move(
                (geometria.width() - VENTANA_ANCHO_DEFAULT) // 2,
                (geometria.height() - VENTANA_ALTO_DEFAULT) // 2,
            )

    # ──────────────────────────────────────────
    # Construcción de la UI
    # ──────────────────────────────────────────

    def _construir_ui(self) -> None:
        """Construye la estructura principal de la ventana."""
        # Widget central
        widget_central = QWidget()
        widget_central.setObjectName("central_widget")
        self.setCentralWidget(widget_central)

        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ── Sidebar ───────────────────────────────
        self._sidebar = Sidebar()
        layout_principal.addWidget(self._sidebar)

        # ── Separador vertical ────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout_principal.addWidget(sep)

        # ── Área de contenido (stacked) ───────────
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_stack")
        layout_principal.addWidget(self._stack, 1)

        # ── Crear y registrar módulos ─────────────
        self._dashboard = DashboardWidget()
        self._registro = RegistroWidget()
        self._historial = HistorialWidget()
        self._estadisticas = EstadisticasWidget()
        self._configuracion = ConfiguracionWidget()

        # Widget de alertas inline
        self._widget_alertas = self._crear_widget_alertas()

        # Widget de ayuda
        self._widget_ayuda = self._crear_widget_ayuda()

        # Mapa módulo → índice en el stack
        self._indice_modulo: dict[str, int] = {}
        for nombre, widget in [
            ("dashboard", self._dashboard),
            ("registro", self._registro),
            ("historial", self._historial),
            ("estadisticas", self._estadisticas),
            ("alertas", self._widget_alertas),
            ("configuracion", self._configuracion),
            ("ayuda", self._widget_ayuda),
        ]:
            idx = self._stack.addWidget(widget)
            self._indice_modulo[nombre] = idx

        # ── Barra de estado ───────────────────────
        self._construir_barra_estado()

        # Aplicar tema inicial
        gestor_tema.aplicar_tema()

    def _construir_barra_estado(self) -> None:
        """Construye la barra de estado inferior."""
        barra = QStatusBar()
        self.setStatusBar(barra)

        # Etiqueta izquierda (mensaje general)
        self._lbl_estado = QLabel(f"{APP_NOMBRE} — Listo")
        barra.addWidget(self._lbl_estado)

        # Separador
        barra.addPermanentWidget(QLabel(" | "))

        # Etiqueta de fecha
        self._lbl_fecha_estado = QLabel()
        self._actualizar_fecha_estado()
        barra.addPermanentWidget(self._lbl_fecha_estado)

        # Etiqueta de alertas
        barra.addPermanentWidget(QLabel(" | "))
        self._lbl_alertas_estado = QLabel()
        barra.addPermanentWidget(self._lbl_alertas_estado)

    def _crear_widget_alertas(self) -> QWidget:
        """Widget inline de listado de alertas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        titulo = QLabel("🔔  Alertas de Salud")
        titulo.setObjectName("titulo_seccion")
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "El sistema analiza automáticamente cada registro y genera alertas "
            "cuando detecta valores fuera de los rangos clínicos recomendados."
        )
        subtitulo.setObjectName("subtitulo_seccion")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        # Botón marcar vistas
        fila_btn = QHBoxLayout()
        self._btn_marcar_vistas = QPushButton("✓  Marcar todas como vistas")
        self._btn_marcar_vistas.setObjectName("btn_secundario")
        self._btn_marcar_vistas.setFixedHeight(36)
        self._btn_marcar_vistas.clicked.connect(self._marcar_alertas_vistas)
        fila_btn.addStretch()
        fila_btn.addWidget(self._btn_marcar_vistas)
        layout.addLayout(fila_btn)

        # Tabla de alertas
        self._tabla_alertas = QTableWidget(0, 5)
        self._tabla_alertas.setHorizontalHeaderLabels(
            ["Fecha", "Métrica", "Valor", "Criticidad", "Descripción"]
        )
        self._tabla_alertas.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._tabla_alertas.setAlternatingRowColors(True)
        self._tabla_alertas.verticalHeader().setVisible(False)
        self._tabla_alertas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._tabla_alertas, 1)

        return widget

    def _crear_widget_ayuda(self) -> QWidget:
        """Widget de ayuda y documentación."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        titulo = QLabel("Ayuda y Soporte")
        titulo.setObjectName("titulo_seccion")
        layout.addWidget(titulo)

        secciones = [
            ("📊 Cómo interpretar las métricas",
             "• Verde: valores normales dentro del rango clínico\n"
             "• Amarillo: atención, valores ligeramente fuera del rango\n"
             "• Naranja: preocupante, considera consultar a tu médico\n"
             "• Rojo: crítico, busca atención médica"),

            ("📅 Cuándo registrar",
             "Se recomienda registrar 3 veces al día:\n"
             "• Mañana: al levantarse, antes de actividad física\n"
             "• Tarde: a mitad del día, después del almuerzo\n"
             "• Noche: antes de dormir, en estado de reposo"),

            ("❤️ Rangos de presión arterial",
             "• Normal: < 120/80 mmHg\n"
             "• Elevada: 120-129/< 80 mmHg\n"
             "• Hipertensión grado 1: 130-139/80-89 mmHg\n"
             "• Hipertensión grado 2: ≥ 140/≥ 90 mmHg\n"
             "• Crisis: > 180/> 120 mmHg (urgencia médica)"),

            ("💾 Exportación y backup",
             "• CSV: tabla de datos sin formato, ideal para análisis\n"
             "• Excel: con formato y colores, ideal para reportes\n"
             "• PDF: reporte formal para compartir con médicos\n"
             "• Backups automáticos en la carpeta /backups"),

            ("🔧 Soporte técnico",
             f"Versión actual: {APP_VERSION}\n"
             "Para reportar problemas o sugerencias:\n"
             "soporte@healthtrackpro.app"),
        ]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(16)

        for titulo_sec, contenido in secciones:
            from PySide6.QtWidgets import QGroupBox
            grupo = QGroupBox(titulo_sec)
            grupo_layout = QVBoxLayout(grupo)
            lbl = QLabel(contenido)
            lbl.setWordWrap(True)
            lbl.setObjectName("subtitulo_seccion")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grupo_layout.addWidget(lbl)
            scroll_layout.addWidget(grupo)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        return widget

    # ──────────────────────────────────────────
    # Conexión de señales
    # ──────────────────────────────────────────

    def _conectar_senales(self) -> None:
        """Conecta todas las señales entre módulos."""
        # Navegación desde sidebar
        self._sidebar.modulo_seleccionado.connect(self._navegar_a)

        # Nuevo registro desde el dashboard
        self._dashboard.solicitar_nuevo_registro.connect(
            lambda: self._navegar_a("registro")
        )

        # Actualizar historial y dashboard al guardar un registro
        self._registro.registro_guardado.connect(self._on_registro_guardado)

        # Cambio de tema desde configuración
        self._configuracion.tema_cambiado.connect(gestor_tema.aplicar_tema)

    # ──────────────────────────────────────────
    # Navegación
    # ──────────────────────────────────────────

    def _navegar_a(self, id_modulo: str) -> None:
        """Muestra el módulo indicado en el área de contenido."""
        if id_modulo not in self._indice_modulo:
            logger.warning("Módulo desconocido: %s", id_modulo)
            return

        self._modulo_actual = id_modulo
        self._stack.setCurrentIndex(self._indice_modulo[id_modulo])
        self._sidebar.activar_modulo(id_modulo)
        self._lbl_estado.setText(f"{APP_NOMBRE} — {id_modulo.capitalize()}")

        # Cargar alertas si se navega al módulo de alertas
        if id_modulo == "alertas":
            self._actualizar_tabla_alertas()

        logger.debug("Navegando a módulo: %s", id_modulo)

    # ──────────────────────────────────────────
    # Actualizaciones periódicas
    # ──────────────────────────────────────────

    def _iniciar_actualizacion_periodica(self) -> None:
        """Timer que actualiza el contador de alertas cada 30 segundos."""
        self._timer_alertas = QTimer(self)
        self._timer_alertas.setInterval(30_000)
        self._timer_alertas.timeout.connect(self._actualizar_contador_alertas)
        self._timer_alertas.start()
        self._actualizar_contador_alertas()

    def _actualizar_contador_alertas(self) -> None:
        """Actualiza el badge de alertas en el sidebar y la barra de estado."""
        conteo = self._servicio_alertas.contar_no_vistas()
        self._sidebar.actualizar_badge_alertas(conteo)

        if conteo > 0:
            self._lbl_alertas_estado.setText(f"⚠ {conteo} alertas pendientes")
            self._lbl_alertas_estado.setStyleSheet("color: #f59e0b;")
        else:
            self._lbl_alertas_estado.setText("✓ Sin alertas pendientes")
            self._lbl_alertas_estado.setStyleSheet("color: #22c55e;")

    def _actualizar_fecha_estado(self) -> None:
        """Actualiza la fecha en la barra de estado."""
        hoy = date.today()
        self._lbl_fecha_estado.setText(hoy.strftime("%d/%m/%Y"))

    def _actualizar_tabla_alertas(self) -> None:
        """Carga las alertas en la tabla del módulo de alertas."""
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtGui import QBrush, QColor
        from core.constants import COLORES_CRITICIDAD

        alertas = self._servicio_alertas.obtener_alertas_activas()
        self._tabla_alertas.setRowCount(len(alertas))

        for i, alerta in enumerate(alertas):
            color = COLORES_CRITICIDAD.get(alerta.criticidad, "#94a3b8")
            datos = [
                alerta.fecha.strftime("%d/%m/%Y") if alerta.fecha else "—",
                alerta.metrica.replace("_", " ").capitalize(),
                alerta.valor or "—",
                alerta.criticidad.capitalize(),
                alerta.descripcion or alerta.titulo,
            ]
            for j, dato in enumerate(datos):
                item = QTableWidgetItem(str(dato))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 3:
                    item.setForeground(QBrush(QColor(color)))
                self._tabla_alertas.setItem(i, j, item)

        self._servicio_alertas.marcar_todas_vistas()
        self._actualizar_contador_alertas()

    def _marcar_alertas_vistas(self) -> None:
        """Marca todas las alertas como vistas."""
        self._servicio_alertas.marcar_todas_vistas()
        self._actualizar_contador_alertas()

    def _on_registro_guardado(self) -> None:
        """Se ejecuta después de guardar un registro nuevo."""
        self._dashboard.actualizar_datos()
        self._historial.actualizar()
        self._actualizar_contador_alertas()
        self._navegar_a("dashboard")

    # ──────────────────────────────────────────
    # Cierre de la aplicación
    # ──────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """Confirma el cierre si hay alertas críticas pendientes."""
        from services.backup_service import ServicioBackup
        from core.config import config

        if config.obtener("backup_automatico", True):
            try:
                ServicioBackup().crear_backup()
                logger.info("Backup automático creado al cerrar")
            except Exception as e:
                logger.warning("No se pudo crear backup automático: %s", e)

        logger.info("Aplicación cerrada por el usuario")
        event.accept()
