"""
Excepciones personalizadas de HealthTrack Pro.

Jerarquía de excepciones que permite manejo granular de errores
en todas las capas de la aplicación.
"""


class HealthTrackError(Exception):
    """Excepción base de la aplicación."""

    def __init__(self, mensaje: str = "Error en HealthTrack Pro") -> None:
        self.mensaje = mensaje
        super().__init__(self.mensaje)


# ──────────────────────────────────────────────
# Errores de base de datos
# ──────────────────────────────────────────────

class BaseDatosError(HealthTrackError):
    """Error en operaciones de base de datos."""


class ConexionError(BaseDatosError):
    """No se pudo establecer conexión con la base de datos."""


class RegistroNoEncontradoError(BaseDatosError):
    """El registro solicitado no existe en la base de datos."""

    def __init__(self, id_registro: int | None = None) -> None:
        mensaje = (
            f"Registro con ID {id_registro} no encontrado"
            if id_registro
            else "Registro no encontrado"
        )
        super().__init__(mensaje)


class DuplicadoError(BaseDatosError):
    """Ya existe un registro para la misma fecha y período."""

    def __init__(self, fecha: str = "", periodo: str = "") -> None:
        mensaje = f"Ya existe un registro para {fecha} en el período '{periodo}'"
        super().__init__(mensaje)


# ──────────────────────────────────────────────
# Errores de validación
# ──────────────────────────────────────────────

class ValidacionError(HealthTrackError):
    """Error de validación de datos de entrada."""

    def __init__(self, campo: str = "", mensaje: str = "") -> None:
        self.campo = campo
        msg = f"Error en campo '{campo}': {mensaje}" if campo else mensaje
        super().__init__(msg)


class ValorFueraDeRangoError(ValidacionError):
    """El valor proporcionado está fuera del rango permitido."""

    def __init__(self, campo: str, valor: float, minimo: float, maximo: float) -> None:
        mensaje = (
            f"El valor {valor} para '{campo}' está fuera del rango "
            f"permitido [{minimo} – {maximo}]"
        )
        super().__init__(campo=campo, mensaje=mensaje)
        self.valor = valor
        self.minimo = minimo
        self.maximo = maximo


# ──────────────────────────────────────────────
# Errores de configuración
# ──────────────────────────────────────────────

class ConfiguracionError(HealthTrackError):
    """Error al leer o escribir configuración."""


class ArchivoConfiguracionError(ConfiguracionError):
    """El archivo de configuración no pudo ser leído o escrito."""


# ──────────────────────────────────────────────
# Errores de exportación
# ──────────────────────────────────────────────

class ExportacionError(HealthTrackError):
    """Error durante la exportación de datos."""

    def __init__(self, formato: str = "", razon: str = "") -> None:
        mensaje = f"Error al exportar en formato {formato}: {razon}" if formato else razon
        super().__init__(mensaje)


# ──────────────────────────────────────────────
# Errores de backup
# ──────────────────────────────────────────────

class BackupError(HealthTrackError):
    """Error al crear o restaurar un backup."""


# ──────────────────────────────────────────────
# Errores de estadísticas
# ──────────────────────────────────────────────

class EstadisticasError(HealthTrackError):
    """Error al calcular estadísticas — datos insuficientes o corruptos."""

    def __init__(self, razon: str = "Datos insuficientes para el cálculo") -> None:
        super().__init__(razon)
