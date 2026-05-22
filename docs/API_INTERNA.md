# API Interna — HealthTrack Pro

Referencia completa de los servicios, repositorios y modelos del sistema.

---

## Servicios

### ServicioRegistro (`services/registro_service.py`)

Gestiona el ciclo de vida completo de los registros de salud.

| Método | Parámetros | Retorno | Descripción |
|--------|-----------|---------|-------------|
| `crear_registro(datos)` | `dict` | `RegistroSalud` | Crea registro nuevo. Lanza `DuplicadoError` si ya existe. |
| `actualizar_registro(id, datos)` | `int, dict` | `RegistroSalud` | Actualiza registro existente. |
| `guardar_o_actualizar(datos)` | `dict` | `tuple[RegistroSalud, bool]` | Crea o actualiza. El bool indica si fue creado. |
| `eliminar_registro(id)` | `int` | `bool` | Elimina. Devuelve False si no existe. |
| `obtener_hoy()` | — | `list[RegistroSalud]` | Registros del día actual. |
| `obtener_por_fecha(fecha)` | `date` | `list[RegistroSalud]` | Registros de una fecha. |
| `obtener_ultimos_dias(dias)` | `int` | `list[RegistroSalud]` | Registros de los últimos N días. |
| `obtener_ultimo()` | — | `RegistroSalud \| None` | El registro más reciente. |
| `fechas_con_registros()` | — | `list[date]` | Fechas que tienen al menos un registro. |
| `total_registros()` | — | `int` | Total de registros en la BD. |

**Formato del dict `datos`:**
```python
{
    "fecha": date,                    # Requerido
    "periodo": str,                   # "manana" | "tarde" | "noche"
    "presion_sistolica": int | None,  # mmHg
    "presion_diastolica": int | None, # mmHg
    "ritmo_cardiaco": int | None,     # bpm
    "oxigenacion": float | None,      # % SpO2
    "peso": float | None,             # kg
    "pasos": int | None,
    "distancia_caminada": float | None,  # km
    "calorias_quemadas": int | None,
    "horas_sueno": float | None,
    "calidad_sueno": int | None,      # 1-10
    "nivel_estres": int | None,       # 1-10
    "estado_animo": int | None,       # 1-10
    "medicamentos": list[str] | None,
    "sintomas": list[str] | None,
    "notas_medicas": str | None,
    "glucosa": float | None,          # mg/dL
    "temperatura_corporal": float | None,  # °C
    "consumo_agua": float | None,     # litros
    "cafeina": int | None,            # mg
    "ejercicio_realizado": str | None,
}
```

---

### ServicioEstadisticas (`services/estadisticas_service.py`)

Cálculos estadísticos sobre series temporales de métricas.

| Método | Parámetros | Retorno | Descripción |
|--------|-----------|---------|-------------|
| `calcular_resumen(metrica, dias)` | `str, int` | `ResumenEstadistico` | Promedio, mediana, max, min, std, tendencia. |
| `serie_temporal(metrica, dias)` | `str, int` | `tuple[list[date], list[float]]` | Serie para gráficas (promedio diario). |
| `series_multiples(metricas, dias)` | `list[str], int` | `dict` | Múltiples series simultáneas. |
| `comparar_periodos(metrica, dias1, dias2)` | `str, int, int` | `dict` | Comparativa entre dos períodos. |
| `obtener_records_historicos()` | — | `list[RecordHistorico]` | Máximos y mínimos históricos. |
| `resumen_hoy()` | — | `dict` | Resumen estadístico del día actual. |

**ResumenEstadistico:**
```python
@dataclass
class ResumenEstadistico:
    metrica: str
    etiqueta: str
    unidad: str
    promedio: float | None
    mediana: float | None
    minimo: float | None
    maximo: float | None
    desviacion_std: float | None
    total_registros: int
    tendencia: str           # "sube" | "baja" | "estable"
    tendencia_porcentaje: float
    fecha_maximo: date | None
    fecha_minimo: date | None
    valores_recientes: list[float]
    fechas_recientes: list[date]
```

**Métricas disponibles en `METRICAS_INFO`:**
```
presion_sistolica, presion_diastolica, ritmo_cardiaco, oxigenacion,
peso, imc, pasos, distancia_caminada, calorias_quemadas,
horas_sueno, calidad_sueno, nivel_estres, estado_animo,
glucosa, temperatura_corporal, consumo_agua, cafeina
```

---

### ServicioAlertas (`services/alertas_service.py`)

Motor de reglas clínicas para generación de alertas.

| Método | Parámetros | Retorno | Descripción |
|--------|-----------|---------|-------------|
| `evaluar_registro(registro)` | `RegistroSalud` | `list[Alerta]` | Evalúa y persiste alertas. |
| `obtener_alertas_activas()` | — | `list[Alerta]` | Alertas no resueltas. |
| `obtener_no_vistas()` | — | `list[Alerta]` | Alertas pendientes de leer. |
| `contar_no_vistas()` | — | `int` | Contador para badge. |
| `marcar_todas_vistas()` | — | `int` | Marca como vistas. Devuelve cantidad. |

---

### ServicioInsights (`services/insights_service.py`)

Genera observaciones automáticas en lenguaje natural.

| Método | Parámetros | Retorno | Descripción |
|--------|-----------|---------|-------------|
| `generar_insights(dias)` | `int` | `list[Insight]` | Hasta 8 insights del período. |

**Insight:**
```python
@dataclass
class Insight:
    icono: str       # Emoji representativo
    texto: str       # Texto en español
    categoria: str   # "cardiovascular"|"fisica"|"sueno"|"mental"|"general"
    positivo: bool   # True=buenas noticias, False=alerta/sugerencia
```

---

### ServicioExportacion (`services/exportacion_service.py`)

| Método | Parámetros | Retorno | Descripción |
|--------|-----------|---------|-------------|
| `exportar_csv(fecha_inicio, fecha_fin, nombre)` | `date|None, date|None, str|None` | `Path` | Exporta a CSV. |
| `exportar_excel(fecha_inicio, fecha_fin, nombre)` | `date|None, date|None, str|None` | `Path` | Exporta a XLSX con formato. |
| `exportar_pdf(fecha_inicio, fecha_fin, nombre)` | `date|None, date|None, str|None` | `Path` | Exporta reporte PDF. |

---

### ServicioBackup (`services/backup_service.py`)

| Método | Parámetros | Retorno | Descripción |
|--------|-----------|---------|-------------|
| `crear_backup()` | — | `Path` | Copia la BD con timestamp. |
| `listar_backups()` | — | `list[Path]` | Lista backups, más reciente primero. |
| `restaurar_backup(ruta)` | `Path` | `None` | Restaura. Hace backup previo automáticamente. |

---

## Modelos

### RegistroSalud

```python
# Propiedades computadas
registro.imc                    # Calculado de peso/altura
registro.medicamentos_lista     # list[str] desde JSON
registro.sintomas_lista         # list[str] desde JSON

# Métodos de criticidad
registro.criticidad_presion()   # str (nivel)
registro.criticidad_ritmo()     # str
registro.criticidad_oxigenacion()  # str
registro.criticidad_imc()       # str
registro.criticidad_general()   # str (el más crítico)

# Serialización
registro.to_dict()              # dict completo
```

### GestorBaseDatos

```python
gestor = GestorBaseDatos()   # Singleton
gestor.verificar_conexion()  # bool
gestor.obtener_ruta()        # Path

with gestor.sesion() as s:
    # Uso de sesión SQLAlchemy
    s.add(entidad)
    # commit automático al salir del with
```

---

## Repositorios

### RepositorioRegistro

```python
repo = RepositorioRegistro(sesion)
repo.obtener_por_id(id)
repo.obtener_por_fecha(fecha)
repo.obtener_por_fecha_y_periodo(fecha, periodo)
repo.obtener_rango(fecha_inicio, fecha_fin)
repo.obtener_ultimos_dias(dias)
repo.obtener_recientes(limite)
repo.obtener_ultimo()
repo.maximo_metrica(metrica)
repo.minimo_metrica(metrica)
repo.promedio_metrica(metrica, fecha_inicio, fecha_fin)
repo.valores_metrica(metrica, fecha_inicio, fecha_fin)
repo.existe_para_fecha_y_periodo(fecha, periodo)
repo.fechas_con_registros(fecha_inicio, fecha_fin)
repo.guardar(registro)
repo.eliminar(registro)
repo.eliminar_por_id(id)
repo.contar()
```

---

## Widgets UI

### GestorTema

```python
from widgets.theme_manager import gestor_tema

gestor_tema.tema_actual     # "oscuro" | "claro"
gestor_tema.es_oscuro       # bool
gestor_tema.colores         # dict con paleta activa
gestor_tema.aplicar_tema("oscuro")   # Aplica tema específico
gestor_tema.alternar()               # Toggle
gestor_tema.tema_cambiado            # Signal(str)
```

### Sidebar

```python
sidebar = Sidebar()
sidebar.modulo_seleccionado   # Signal(str)
sidebar.activar_modulo(id)    # Activa visualmente
sidebar.actualizar_badge_alertas(n)  # Badge del botón alertas
```

### TarjetaMetrica

```python
tarjeta = TarjetaMetrica("Presión Arterial", "mmHg")
tarjeta.actualizar(
    valor="120/80",
    criticidad="normal",
    tendencia="baja",    # "sube"|"baja"|"estable"
    tendencia_pct=3.2,
    subtexto="Texto opcional",
)
tarjeta.limpiar()  # Estado vacío
```

### GraficaLineaTemporal

```python
from charts.linea_temporal import GraficaLineaTemporal

grafica = GraficaLineaTemporal(titulo="Mi gráfica", unidad="mmHg")
grafica.agregar_serie(fechas, valores, "Mi métrica", "#6366f1")
grafica.establecer_zona_normal(60, 120)
grafica.establecer_zona_peligro(140)
grafica.dibujar()
grafica.limpiar_series()
grafica.cambiar_tema(oscuro=True)
```

---

## Excepciones

```python
from core.exceptions import (
    HealthTrackError,        # Base
    BaseDatosError,          # Error de BD
    ConexionError,           # Sin conexión
    RegistroNoEncontradoError,  # ID no existe
    DuplicadoError,          # Fecha+período repetido
    ValidacionError,         # Campo inválido
    ValorFueraDeRangoError,  # Valor numérico fuera de rango
    ConfiguracionError,      # Error de config
    ExportacionError,        # Error al exportar
    BackupError,             # Error de backup
    EstadisticasError,       # Datos insuficientes
)
```
