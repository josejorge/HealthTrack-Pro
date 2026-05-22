"""
Widget de configuración de la aplicación.

Permite al usuario personalizar su perfil, preferencias de UI,
umbrales de alerta y opciones de backup.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from services.backup_service import ServicioBackup
from widgets.theme_manager import gestor_tema
from core.config import config

logger = logging.getLogger("healthtrack.ui.configuracion")


class ConfiguracionWidget(QWidget):
    """Panel de configuración de la aplicación."""

    tema_cambiado = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._servicio_backup = ServicioBackup()
        self._construir_ui()
        self._cargar_valores()

    def _construir_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        contenedor = QWidget()
        scroll.setWidget(contenedor)

        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("Configuración")
        titulo.setObjectName("titulo_seccion")
        layout.addWidget(titulo)

        # Secciones
        layout.addWidget(self._crear_seccion_perfil())
        layout.addWidget(self._crear_seccion_apariencia())
        layout.addWidget(self._crear_seccion_objetivos())
        layout.addWidget(self._crear_seccion_backup())

        # Botón guardar
        fila_btn = QHBoxLayout()
        fila_btn.addStretch()
        btn_guardar = QPushButton("✓  Guardar Configuración")
        btn_guardar.setObjectName("btn_primario")
        btn_guardar.setFixedHeight(42)
        btn_guardar.setFixedWidth(220)
        btn_guardar.clicked.connect(self._guardar)
        fila_btn.addWidget(btn_guardar)
        layout.addLayout(fila_btn)
        layout.addStretch()

        layout_ext = QVBoxLayout(self)
        layout_ext.setContentsMargins(0, 0, 0, 0)
        layout_ext.addWidget(scroll)

    def _crear_seccion_perfil(self) -> QGroupBox:
        grupo = QGroupBox("  👤  Perfil del Usuario")
        form = QFormLayout(grupo)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._input_nombre = QLineEdit()
        self._input_nombre.setPlaceholderText("Tu nombre")
        form.addRow("Nombre:", self._input_nombre)

        self._spin_altura = QSpinBox()
        self._spin_altura.setRange(50, 300)
        self._spin_altura.setSuffix(" cm")
        form.addRow("Altura:", self._spin_altura)

        return grupo

    def _crear_seccion_apariencia(self) -> QGroupBox:
        grupo = QGroupBox("  🎨  Apariencia")
        layout = QVBoxLayout(grupo)
        layout.setSpacing(12)

        fila_tema = QHBoxLayout()
        lbl_tema = QLabel("Tema de la aplicación:")
        lbl_tema.setObjectName("etiqueta_campo")
        fila_tema.addWidget(lbl_tema)

        self._btn_tema_oscuro = QPushButton("Modo Oscuro")
        self._btn_tema_oscuro.setObjectName("btn_primario" if gestor_tema.es_oscuro else "btn_secundario")
        self._btn_tema_oscuro.setFixedWidth(130)
        self._btn_tema_oscuro.clicked.connect(lambda: self._cambiar_tema("oscuro"))

        self._btn_tema_claro = QPushButton("Modo Claro")
        self._btn_tema_claro.setObjectName("btn_primario" if not gestor_tema.es_oscuro else "btn_secundario")
        self._btn_tema_claro.setFixedWidth(130)
        self._btn_tema_claro.clicked.connect(lambda: self._cambiar_tema("claro"))

        fila_tema.addWidget(self._btn_tema_oscuro)
        fila_tema.addWidget(self._btn_tema_claro)
        fila_tema.addStretch()
        layout.addLayout(fila_tema)

        return grupo

    def _crear_seccion_objetivos(self) -> QGroupBox:
        grupo = QGroupBox("  🎯  Objetivos Diarios")
        form = QFormLayout(grupo)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._spin_pasos_obj = QSpinBox()
        self._spin_pasos_obj.setRange(1000, 50000)
        self._spin_pasos_obj.setSingleStep(500)
        self._spin_pasos_obj.setSuffix(" pasos")
        form.addRow("Objetivo de pasos:", self._spin_pasos_obj)

        self._spin_agua_obj = QDoubleSpinBox()
        self._spin_agua_obj.setRange(0.5, 10.0)
        self._spin_agua_obj.setSingleStep(0.25)
        self._spin_agua_obj.setSuffix(" L")
        form.addRow("Objetivo de agua:", self._spin_agua_obj)

        self._spin_peso_obj = QDoubleSpinBox()
        self._spin_peso_obj.setRange(30.0, 300.0)
        self._spin_peso_obj.setSuffix(" kg")
        form.addRow("Peso objetivo:", self._spin_peso_obj)

        return grupo

    def _crear_seccion_backup(self) -> QGroupBox:
        grupo = QGroupBox("  💾  Copia de Seguridad")
        layout = QVBoxLayout(grupo)
        layout.setSpacing(12)

        self._check_backup_auto = QCheckBox("Realizar copia de seguridad automática")
        layout.addWidget(self._check_backup_auto)

        fila_btn_backup = QHBoxLayout()

        btn_backup_ahora = QPushButton("💾  Crear Backup Ahora")
        btn_backup_ahora.setObjectName("btn_secundario")
        btn_backup_ahora.setFixedHeight(36)
        btn_backup_ahora.clicked.connect(self._crear_backup)
        fila_btn_backup.addWidget(btn_backup_ahora)

        self._lbl_backups = QLabel()
        self._lbl_backups.setObjectName("subtitulo_seccion")
        fila_btn_backup.addWidget(self._lbl_backups)
        fila_btn_backup.addStretch()

        layout.addLayout(fila_btn_backup)
        self._actualizar_info_backups()
        return grupo

    # ──────────────────────────────────────────
    # Datos
    # ──────────────────────────────────────────

    def _cargar_valores(self) -> None:
        """Carga los valores actuales de configuración en los campos."""
        self._input_nombre.setText(config.usuario_nombre)
        self._spin_altura.setValue(config.usuario_altura)
        self._spin_pasos_obj.setValue(config.usuario_pasos_objetivo)
        self._spin_agua_obj.setValue(config.usuario_agua_objetivo)
        self._spin_peso_obj.setValue(config.obtener("usuario_peso_objetivo", 70.0))
        self._check_backup_auto.setChecked(config.obtener("backup_automatico", True))

    def _guardar(self) -> None:
        """Persiste todos los valores del formulario."""
        config.usuario_nombre = self._input_nombre.text().strip() or "Usuario"
        config.usuario_altura = self._spin_altura.value()
        config.establecer("usuario_pasos_objetivo", self._spin_pasos_obj.value())
        config.establecer("usuario_agua_objetivo", self._spin_agua_obj.value())
        config.establecer("usuario_peso_objetivo", self._spin_peso_obj.value())
        config.establecer("backup_automatico", self._check_backup_auto.isChecked())

        QMessageBox.information(self, "Configuración guardada", "Los cambios se han guardado correctamente.")
        logger.info("Configuración guardada por el usuario")

    def _cambiar_tema(self, nombre: str) -> None:
        """Cambia el tema visual."""
        gestor_tema.aplicar_tema(nombre)
        self.tema_cambiado.emit(nombre)
        # Actualizar estado visual de botones
        self._btn_tema_oscuro.setObjectName("btn_primario" if nombre == "oscuro" else "btn_secundario")
        self._btn_tema_claro.setObjectName("btn_primario" if nombre == "claro" else "btn_secundario")
        for btn in [self._btn_tema_oscuro, self._btn_tema_claro]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _crear_backup(self) -> None:
        """Crea un backup manual."""
        try:
            ruta = self._servicio_backup.crear_backup()
            self._actualizar_info_backups()
            QMessageBox.information(
                self, "Backup creado",
                f"Copia de seguridad guardada en:\n{ruta}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error de backup", str(e))

    def _actualizar_info_backups(self) -> None:
        """Actualiza el texto de información de backups."""
        backups = self._servicio_backup.listar_backups()
        self._lbl_backups.setText(f"{len(backups)} copias disponibles")
