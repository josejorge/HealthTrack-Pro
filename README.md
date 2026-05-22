# HealthTrack Pro

> Aplicación de escritorio profesional para Windows que permite registrar, visualizar y analizar métricas de salud personal con gráficas interactivas, alertas inteligentes e insights automáticos.

---

## Características Principales

| Módulo | Descripción |
|--------|-------------|
| **Dashboard** | Resumen del día, tarjetas de métricas con color por criticidad, gráficas de tendencia |
| **Registro** | Formulario completo para mañana/tarde/noche con validación en tiempo real |
| **Historial** | Calendario interactivo con días resaltados y tabla por fecha |
| **Estadísticas** | Gráficas por período, promedios, medianas, récords históricos |
| **Alertas** | Motor clínico automático con recomendaciones personalizadas |
| **Exportación** | PDF, CSV y Excel de todos los registros |
| **Configuración** | Tema oscuro/claro, perfil, objetivos, backup automático |

## Métricas Monitoreadas

**Cardiovascular:** Presión arterial (sistólica/diastólica), ritmo cardíaco, oxigenación SpO2

**Física:** Peso, IMC (calculado), pasos, distancia, calorías quemadas

**Descanso:** Horas de sueño, calidad del sueño (1–10)

**Mental:** Nivel de estrés, estado de ánimo (1–10)

**Médica:** Medicamentos, síntomas, notas médicas

**Adicional:** Glucosa, temperatura corporal, agua, cafeína, ejercicio

## Sistema de Criticidad

```
🟢 NORMAL      — Valores dentro del rango clínico recomendado
🟡 ATENCIÓN    — Valores ligeramente fuera del rango
🟠 PREOCUPANTE — Valores que requieren seguimiento médico
🔴 CRÍTICO     — Valores que requieren atención médica urgente
```

## Instalación

### Requisitos

- Python 3.12+
- Windows 10/11

### Instalación del entorno de desarrollo

```bash
# Clonar o descomprimir el proyecto
cd "HealthTrack Pro"

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# (Opcional) Generar datos demo
python scripts/seed_data.py

# Ejecutar la aplicación
python main.py
```

### Dependencias de desarrollo

```bash
pip install -r requirements-dev.txt
```

## Estructura del Proyecto

```
HealthTrack Pro/
├── main.py                    # Punto de entrada
├── app/                       # Ciclo de vida de la aplicación
├── core/                      # Infraestructura: config, logger, constantes
├── database/                  # Conexión SQLite y repositorios
├── models/                    # Modelos SQLAlchemy
├── services/                  # Lógica de negocio
├── ui/                        # Módulos de interfaz gráfica
│   ├── dashboard/             # Panel principal
│   ├── registro/              # Formulario de registro
│   ├── historial/             # Vista de historial
│   ├── estadisticas/          # Gráficas y estadísticas
│   └── configuracion/         # Preferencias
├── widgets/                   # Componentes UI reutilizables
├── charts/                    # Clases de gráficas matplotlib
├── scripts/                   # Scripts utilitarios
├── tests/                     # Suite de pruebas
├── docs/                      # Documentación técnica
├── backups/                   # Copias de seguridad automáticas
├── exports/                   # Archivos exportados
└── logs/                      # Logs de la aplicación
```

## Uso Rápido

1. **Primer uso:** Ejecuta `python scripts/seed_data.py` para generar datos demo.
2. **Registrar:** Haz clic en "Nuevo Registro" → Completa los campos → Guardar.
3. **Ver tendencias:** Ve a "Estadísticas" y selecciona el período.
4. **Exportar:** En "Historial" → botón "Exportar" o en "Estadísticas" → PDF/Excel.

## Tests

```bash
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

## Compilación EXE

```bash
pip install pyinstaller
python scripts/build_exe.py
# Resultado: dist/HealthTrackPro.exe
```

## Tecnologías

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| Python | 3.12+ | Lenguaje principal |
| PySide6 | 6.6+ | Interfaz gráfica Qt |
| SQLAlchemy | 2.0+ | ORM para SQLite |
| Matplotlib | 3.8+ | Gráficas embebidas |
| NumPy | 1.26+ | Cálculos numéricos |
| Pandas | 2.1+ | Análisis de datos |
| ReportLab | 4.0+ | Generación de PDF |
| openpyxl | 3.1+ | Generación de Excel |

## Roadmap

- [ ] Integración con smartwatches (Garmin, Fitbit, Apple Watch)
- [ ] Sincronización cloud opcional
- [ ] Modo multiusuario
- [ ] Análisis predictivo con IA
- [ ] API REST para integraciones externas
- [ ] App móvil complementaria (Flutter)
- [ ] Integración con historiales médicos electrónicos

## Arquitectura

La aplicación sigue el patrón **MVC** con separación estricta de capas:

```
UI (PySide6)
    ↓ invoca
Servicios (lógica de negocio)
    ↓ usa
Repositorios (acceso a datos)
    ↓ opera sobre
Modelos SQLAlchemy (entidades)
    ↓ persiste en
SQLite (base de datos)
```

## Soporte

- Documentación técnica: `docs/DOCUMENTACION_TECNICA.md`
- Guía del desarrollador: `docs/GUIA_DESARROLLADOR.md`
- Email: soporte@healthtrackpro.app

## Licencia

MIT License — ver `LICENSE` para detalles.

---

*Desarrollado con Python, PySide6 y mucho cuidado por la salud de los usuarios.*
