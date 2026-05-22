# Documentación Técnica — HealthTrack Pro

## Arquitectura General

HealthTrack Pro sigue el patrón **MVC** (Model-View-Controller) con una capa de servicios adicional que encapsula la lógica de negocio.

```
┌─────────────────────────────────────────────────┐
│                   UI LAYER                       │
│  DashboardWidget │ RegistroWidget │ ...          │
│  (PySide6 / QSS Styling)                        │
└────────────────────┬────────────────────────────┘
                     │ invoca métodos
┌────────────────────▼────────────────────────────┐
│               SERVICE LAYER                      │
│  ServicioRegistro │ ServicioEstadisticas │ ...  │
│  (Lógica de negocio, validación, cálculos)      │
└────────────────────┬────────────────────────────┘
                     │ delega persistencia
┌────────────────────▼────────────────────────────┐
│             REPOSITORY LAYER                     │
│  RepositorioRegistro │ RepositorioAlerta        │
│  (Consultas SQL via SQLAlchemy)                 │
└────────────────────┬────────────────────────────┘
                     │ mapea a/desde tablas
┌────────────────────▼────────────────────────────┐
│               MODEL LAYER                        │
│  RegistroSalud │ Alerta │ ConfiguracionUsuario  │
│  (SQLAlchemy ORM entities)                      │
└────────────────────┬────────────────────────────┘
                     │ persiste en
┌────────────────────▼────────────────────────────┐
│            DATABASE (SQLite)                     │
│  database/healthtrack.db                        │
└─────────────────────────────────────────────────┘
```

## Esquema de Base de Datos

### Tabla: registros_salud

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER PK | Identificador único |
| fecha | DATE | Fecha del registro (índice) |
| periodo | VARCHAR(10) | 'manana', 'tarde', 'noche' |
| presion_sistolica | INTEGER | mmHg, nullable |
| presion_diastolica | INTEGER | mmHg, nullable |
| ritmo_cardiaco | INTEGER | bpm, nullable |
| oxigenacion | FLOAT | % SpO2, nullable |
| peso | FLOAT | kg, nullable |
| altura | FLOAT | cm, nullable |
| imc | FLOAT | Calculado automáticamente |
| pasos | INTEGER | nullable |
| distancia_caminada | FLOAT | km, nullable |
| calorias_quemadas | INTEGER | kcal, nullable |
| horas_sueno | FLOAT | horas, nullable |
| calidad_sueno | INTEGER | 1-10, nullable |
| nivel_estres | INTEGER | 1-10, nullable |
| estado_animo | INTEGER | 1-10, nullable |
| medicamentos | TEXT | JSON array, nullable |
| notas_medicas | TEXT | nullable |
| sintomas | TEXT | JSON array, nullable |
| glucosa | FLOAT | mg/dL, nullable |
| temperatura_corporal | FLOAT | °C, nullable |
| consumo_agua | FLOAT | litros, nullable |
| cafeina | INTEGER | mg, nullable |
| ejercicio_realizado | TEXT | nullable |
| fecha_creacion | DATETIME | Auto |
| fecha_actualizacion | DATETIME | Auto-update |

**Restricción única:** (fecha, periodo)

### Tabla: alertas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER PK | |
| registro_id | INTEGER | FK a registros_salud |
| fecha | DATE | |
| metrica | VARCHAR(100) | Nombre de la métrica |
| valor | VARCHAR(50) | Valor que disparó la alerta |
| criticidad | VARCHAR(20) | normal/atencion/preocupante/critico |
| titulo | VARCHAR(200) | Título legible |
| descripcion | TEXT | Descripción detallada |
| recomendacion | TEXT | Acción recomendada |
| vista | BOOLEAN | Si fue leída por el usuario |
| resuelta | BOOLEAN | Si fue marcada como resuelta |
| fecha_creacion | DATETIME | Auto |

## Flujo de Datos — Registro de Salud

```
Usuario completa formulario (RegistroWidget)
    ↓
_recopilar_datos() → dict con todos los campos
    ↓
ServicioRegistro.guardar_o_actualizar(datos)
    ↓
_construir_registro(datos) → RegistroSalud
    ↓
calcular_y_guardar_imc() → calcula IMC
    ↓
RepositorioRegistro.guardar(registro)
    ↓
SQLAlchemy → INSERT INTO registros_salud
    ↓
ServicioAlertas.evaluar_registro(registro)
    ↓
Motor de reglas → genera Alerta si aplica
    ↓
RepositorioAlerta.guardar(alerta)
    ↓
registro_guardado.emit() → Dashboard se actualiza
```

## Motor de Alertas — Umbrales Clínicos

Basados en guías AHA/ESC 2023:

### Presión Arterial

| Categoría | Sistólica | Diastólica | Criticidad |
|-----------|-----------|------------|------------|
| Normal | < 120 | < 80 | Normal |
| Elevada | 120–129 | < 80 | — |
| Hipertensión 1 | 130–139 | 80–89 | Atención |
| Hipertensión 2 | ≥ 140 | ≥ 90 | Preocupante |
| Crisis | ≥ 180 | ≥ 120 | Crítico |

### Oxigenación SpO2

| Rango | Criticidad |
|-------|------------|
| ≥ 95% | Normal |
| 90–94% | Atención |
| < 90% | Crítico |

## Sistema de Temas (QSS)

El gestor de temas (`GestorTema`) genera dinámicamente hojas de estilo QSS completas a partir de la paleta de colores activa. Esto permite cambiar el tema sin reiniciar la aplicación.

```python
gestor_tema.alternar()    # Alterna oscuro/claro
gestor_tema.aplicar_tema("oscuro")  # Aplica específico
```

## Extensibilidad

### Agregar una nueva métrica

1. Agregar columna al modelo `RegistroSalud` en `models/registro_salud.py`
2. Agregar al mapa `METRICAS_INFO` en `ServicioEstadisticas`
3. Agregar campo al formulario en `RegistroWidget`
4. Agregar regla en `ServicioAlertas` si aplica
5. Agregar tarjeta en `DashboardWidget` si es métrica principal

### Agregar un nuevo gráfico

1. Crear clase en `charts/` heredando de `GraficaBase`
2. Implementar `dibujar()`
3. Instanciar en el widget de UI correspondiente
