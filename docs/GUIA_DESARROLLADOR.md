# Guía del Desarrollador — HealthTrack Pro

Esta guía explica cómo configurar el entorno de desarrollo,
extender el sistema y seguir las convenciones del proyecto.

---

## Configuración del Entorno

### 1. Requisitos previos

- Python 3.12 o superior
- pip actualizado: `python -m pip install --upgrade pip`
- Git configurado

### 2. Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/healthtrack-pro.git
cd "healthtrack-pro"

# Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Verificar instalación (debe abrir la app)
python main.py
```

### 3. Datos de prueba

```bash
# Genera 60 días de registros simulados
python scripts/seed_data.py
```

---

## Convenciones de Código

### Estilo general

- **Línea máxima:** 100 caracteres
- **Formateo:** `black` (`black .`)
- **Linting:** `ruff` (`ruff check .`)
- **Tipado:** Type hints en todos los métodos públicos

### Idioma del código

- **Comentarios y docstrings:** Español
- **Nombres de variables/funciones:** Español (snake_case)
- **Nombres de clases:** Español (PascalCase)
- **Mensajes de usuario:** Español
- **Mensajes de logging:** Español

### Ejemplos de nomenclatura

```python
# ✓ Correcto
def obtener_registros_por_fecha(fecha: date) -> list[RegistroSalud]: ...
clase ServicioEstadisticas: ...
self._servicio_alertas = ServicioAlertas()

# ✗ Incorrecto
def getRecordsByDate(fecha: date) -> list[RegistroSalud]: ...
class StatisticsService: ...
```

### Docstrings

```python
def calcular_resumen(self, metrica: str, dias: int = 30) -> ResumenEstadistico:
    """
    Calcula un resumen estadístico completo para una métrica.

    Args:
        metrica: Nombre del campo en RegistroSalud (ej. 'presion_sistolica').
        dias: Cuántos días hacia atrás incluir en el análisis.

    Returns:
        ResumenEstadistico con promedio, mediana, tendencia y récords.

    Raises:
        EstadisticasError: Si la métrica no es válida.
    """
```

---

## Agregar una Nueva Métrica de Salud

Ejemplo: agregar "saturación de CO2" (`saturacion_co2`).

### Paso 1 — Modelo (`models/registro_salud.py`)

```python
# En RegistroSalud, agregar la columna:
saturacion_co2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # %

# Agregar al método to_dict():
"saturacion_co2": self.saturacion_co2,
```

### Paso 2 — Estadísticas (`services/estadisticas_service.py`)

```python
# En METRICAS_INFO:
"saturacion_co2": ("Saturación CO2", "%"),
```

### Paso 3 — Formulario (`ui/registro/registro_widget.py`)

```python
# En _crear_grupo_opcional():
layout.addWidget(_crear_etiqueta("Saturación CO2"))
self._spin_co2 = _crear_spin_decimal(0.0, 10.0, 1, 0.1, "%")
layout.addWidget(self._spin_co2)

# En _recopilar_datos():
"saturacion_co2": spin_valor_decimal(self._spin_co2),

# En limpiar_formulario():
self._spin_co2.setValue(self._spin_co2.minimum())
```

### Paso 4 — Alertas (`services/alertas_service.py`) — si aplica

```python
def _evaluar_co2(self, registro: RegistroSalud) -> Optional[Alerta]:
    co2 = registro.saturacion_co2
    if co2 is None:
        return None
    if co2 > 5.0:
        return self._crear_alerta(
            registro=registro,
            metrica="saturacion_co2",
            valor=f"{co2}%",
            criticidad=CRITICIDAD_PREOCUPANTE,
            titulo="CO2 elevado",
            descripcion=f"Saturación de CO2: {co2}%.",
            recomendacion="Consulta a tu médico.",
        )
    return None

# Y agregar al método evaluar_registro():
evaluadores = [..., self._evaluar_co2]
```

### Paso 5 — Dashboard (`ui/dashboard/dashboard_widget.py`) — opcional

Si es una métrica importante, agregar una TarjetaMetrica adicional.

### Paso 6 — Migración de base de datos

SQLAlchemy con `create_all` agrega columnas automáticamente en la siguiente ejecución si la tabla ya existe (para SQLite, solo agrega tablas nuevas, no columnas). Para columnas nuevas en producción, usa Alembic o ALTER TABLE manual.

---

## Agregar un Nuevo Tipo de Gráfica

### 1. Crear la clase en `charts/`

```python
# charts/mi_grafica.py
from charts.base_chart import GraficaBase

class MiGrafica(GraficaBase):
    def __init__(self, parent=None) -> None:
        super().__init__(titulo="Mi Gráfica", parent=parent)
        self._datos = []

    def cargar_datos(self, datos: list) -> None:
        self._datos = datos
        self.dibujar()

    def dibujar(self) -> None:
        self.limpiar()
        if not self._datos:
            return
        # ... lógica matplotlib ...
        self.refrescar()
```

### 2. Instanciar en el widget correspondiente

```python
from charts.mi_grafica import MiGrafica

self._mi_grafica = MiGrafica()
self._mi_grafica.cargar_datos(mis_datos)
layout.addWidget(self._mi_grafica)
```

---

## Agregar un Nuevo Módulo de UI

### 1. Crear el widget

```python
# ui/mi_modulo/mi_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MiWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Mi Módulo"))
```

### 2. Registrar en la sidebar (`widgets/sidebar.py`)

```python
ITEMS_NAV = [
    ...
    ("mi_modulo", "Mi Módulo", "🔍", "Descripción del módulo"),
]
```

### 3. Agregar al stack en la ventana principal (`ui/main_window.py`)

```python
from ui.mi_modulo.mi_widget import MiWidget

self._mi_widget = MiWidget()
# En el mapa de módulos:
("mi_modulo", self._mi_widget),
```

---

## Sistema de Logging

```python
import logging
logger = logging.getLogger("healthtrack.mi_modulo")

logger.debug("Mensaje de depuración (solo en modo debug)")
logger.info("Operación completada: %s", detalle)
logger.warning("Situación inesperada: %s", razon)
logger.error("Error recuperable: %s", error, exc_info=True)
logger.critical("Error fatal: %s", error)
```

Los logs se guardan en:
- `logs/healthtrack.log` — todos los niveles INFO+
- `logs/errores.log` — solo ERROR y CRITICAL

---

## Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Solo un módulo
pytest tests/test_models.py -v

# Tests con palabra clave
pytest -k "presion" -v
```

### Agregar un test

```python
# tests/test_mi_modulo.py
import pytest
from mi_modulo import MiClase

class TestMiClase:
    def test_comportamiento_esperado(self):
        instancia = MiClase()
        resultado = instancia.mi_metodo()
        assert resultado == valor_esperado
```

---

## Compilar el EXE

```bash
# Instalar PyInstaller
pip install pyinstaller

# Compilar (genera dist/HealthTrackPro.exe)
python scripts/build_exe.py
```

El ejecutable incluye todas las dependencias y no requiere Python instalado.

---

## Convención de Commits Git

```
tipo(alcance): descripción breve en español

Tipos:
  feat     — Nueva funcionalidad
  fix      — Corrección de bug
  refactor — Refactorización sin cambio funcional
  docs     — Cambios en documentación
  test     — Agregar o modificar tests
  style    — Formato, espacios, sin cambio lógico
  chore    — Tareas de mantenimiento

Ejemplos:
  feat(registro): agregar campo de saturación CO2
  fix(alertas): corregir umbral de glucosa para prediabetes
  docs(readme): actualizar instrucciones de instalación
  test(modelos): agregar tests de validación de IMC
```

---

## Estructura de Branches

```
main          ← Producción estable
develop       ← Integración de features
feature/*     ← Nuevas funcionalidades
fix/*         ← Corrección de bugs
release/*     ← Preparación de versión
```
