"""
Gestión centralizada de configuración de HealthTrack Pro.

Lee y escribe preferencias del usuario desde/hacia un archivo JSON.
Proporciona valores por defecto seguros para todas las opciones.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from core.exceptions import ArchivoConfiguracionError

logger = logging.getLogger("healthtrack.config")

# Ruta del archivo de configuración
RUTA_CONFIG = Path(__file__).parent.parent / "config" / "settings.json"

# Configuración por defecto completa
CONFIGURACION_DEFAULT: dict[str, Any] = {
    # Apariencia
    "tema": "oscuro",           # "oscuro" | "claro"
    "idioma": "es",
    "fuente_tamano": 13,

    # Perfil del usuario
    "usuario_nombre": "Usuario",
    "usuario_altura": 170,      # cm (necesaria para calcular IMC)
    "usuario_peso_objetivo": 70.0,  # kg
    "usuario_pasos_objetivo": 10000,
    "usuario_agua_objetivo": 2.5,   # litros

    # Base de datos
    "db_ruta": "database/healthtrack.db",

    # Backups
    "backup_automatico": True,
    "backup_intervalo_dias": 7,
    "backup_directorio": "backups",
    "backup_max_copias": 10,

    # Notificaciones
    "notificaciones_habilitadas": True,
    "recordatorio_manana": "08:00",
    "recordatorio_tarde": "14:00",
    "recordatorio_noche": "21:00",

    # Alertas
    "alertas_habilitadas": True,
    "alerta_presion_sistolica_max": 140,
    "alerta_presion_diastolica_max": 90,
    "alerta_ritmo_min": 50,
    "alerta_ritmo_max": 110,
    "alerta_oxigenacion_min": 94,
    "alerta_glucosa_max": 126,
    "alerta_temperatura_max": 38.0,

    # Exportación
    "exportacion_directorio": "exports",
    "exportacion_incluir_graficas": True,

    # Dashboard
    "dashboard_dias_tendencia": 7,
    "dashboard_metricas_favoritas": [
        "presion_sistolica", "presion_diastolica",
        "ritmo_cardiaco", "oxigenacion",
        "peso", "pasos",
    ],

    # Gráficas
    "grafica_periodo_default": "30d",
    "grafica_animaciones": True,

    # Desarrollo
    "debug": False,
}


class Configuracion:
    """
    Singleton que gestiona la configuración de la aplicación.

    Lee el archivo JSON al iniciar y provee acceso tipado a cada opción.
    Los cambios se persisten inmediatamente en disco.
    """

    _instancia: Configuracion | None = None
    _datos: dict[str, Any] = {}

    def __new__(cls) -> "Configuracion":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._cargar()
        return cls._instancia

    # ──────────────────────────────────────────
    # Inicialización
    # ──────────────────────────────────────────

    def _cargar(self) -> None:
        """Carga configuración desde disco o crea el archivo con valores por defecto."""
        self._datos = dict(CONFIGURACION_DEFAULT)

        if RUTA_CONFIG.exists():
            try:
                with RUTA_CONFIG.open("r", encoding="utf-8") as f:
                    guardada = json.load(f)
                # Mezcla: valores guardados sobreescriben los default
                self._datos.update(guardada)
                logger.info("Configuración cargada desde %s", RUTA_CONFIG)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Error al leer configuración: %s — usando valores por defecto", e)
        else:
            self._guardar()
            logger.info("Configuración creada con valores por defecto")

    def _guardar(self) -> None:
        """Persiste la configuración actual en disco."""
        try:
            RUTA_CONFIG.parent.mkdir(parents=True, exist_ok=True)
            with RUTA_CONFIG.open("w", encoding="utf-8") as f:
                json.dump(self._datos, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise ArchivoConfiguracionError(
                f"No se pudo guardar la configuración: {e}"
            ) from e

    # ──────────────────────────────────────────
    # Acceso genérico
    # ──────────────────────────────────────────

    def obtener(self, clave: str, defecto: Any = None) -> Any:
        """Obtiene un valor de configuración por clave."""
        return self._datos.get(clave, defecto)

    def establecer(self, clave: str, valor: Any) -> None:
        """Establece un valor y lo persiste inmediatamente."""
        self._datos[clave] = valor
        self._guardar()
        logger.debug("Configuración actualizada: %s = %s", clave, valor)

    def restablecer(self) -> None:
        """Restaura todos los valores por defecto y los guarda."""
        self._datos = dict(CONFIGURACION_DEFAULT)
        self._guardar()
        logger.info("Configuración restablecida a valores por defecto")

    # ──────────────────────────────────────────
    # Propiedades tipadas (acceso directo)
    # ──────────────────────────────────────────

    @property
    def tema(self) -> str:
        return self._datos.get("tema", "oscuro")

    @tema.setter
    def tema(self, valor: str) -> None:
        self.establecer("tema", valor)

    @property
    def usuario_nombre(self) -> str:
        return self._datos.get("usuario_nombre", "Usuario")

    @usuario_nombre.setter
    def usuario_nombre(self, valor: str) -> None:
        self.establecer("usuario_nombre", valor)

    @property
    def usuario_altura(self) -> int:
        return self._datos.get("usuario_altura", 170)

    @usuario_altura.setter
    def usuario_altura(self, valor: int) -> None:
        self.establecer("usuario_altura", valor)

    @property
    def db_ruta(self) -> Path:
        ruta_relativa = self._datos.get("db_ruta", "database/healthtrack.db")
        return Path(__file__).parent.parent / ruta_relativa

    @property
    def backup_directorio(self) -> Path:
        return Path(__file__).parent.parent / self._datos.get("backup_directorio", "backups")

    @property
    def exportacion_directorio(self) -> Path:
        return Path(__file__).parent.parent / self._datos.get("exportacion_directorio", "exports")

    @property
    def debug(self) -> bool:
        return bool(self._datos.get("debug", False))

    @property
    def notificaciones_habilitadas(self) -> bool:
        return bool(self._datos.get("notificaciones_habilitadas", True))

    @property
    def alertas_habilitadas(self) -> bool:
        return bool(self._datos.get("alertas_habilitadas", True))

    @property
    def dashboard_dias_tendencia(self) -> int:
        return int(self._datos.get("dashboard_dias_tendencia", 7))

    @property
    def grafica_periodo_default(self) -> str:
        return self._datos.get("grafica_periodo_default", "30d")

    @property
    def usuario_pasos_objetivo(self) -> int:
        return int(self._datos.get("usuario_pasos_objetivo", 10000))

    @property
    def usuario_agua_objetivo(self) -> float:
        return float(self._datos.get("usuario_agua_objetivo", 2.5))

    def __repr__(self) -> str:
        return f"Configuracion(tema={self.tema!r}, usuario={self.usuario_nombre!r})"


# Instancia global — importar desde cualquier módulo
config = Configuracion()
