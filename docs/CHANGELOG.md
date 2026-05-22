# Changelog — HealthTrack Pro

Todos los cambios notables de este proyecto serán documentados aquí.
El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y el proyecto sigue [Versionado Semántico](https://semver.org/lang/es/).

---

## [1.0.0] — 2026-05-22

### Añadido

#### Core
- Sistema de configuración JSON con valores por defecto
- Logger profesional con rotación de archivos (5 MB, 5 copias)
- Sistema de excepciones personalizadas con jerarquía completa
- Constantes clínicas basadas en guías AHA/ESC 2023

#### Base de Datos
- Modelo `RegistroSalud` con 25+ campos de métricas de salud
- Restricción única por (fecha, período)
- Cálculo automático de IMC al guardar peso/altura
- Modelo `Alerta` con sistema de criticidad
- Repositorios con patrón Repository para acceso a datos
- Base de datos SQLite con WAL mode y foreign keys habilitadas

#### Servicios
- `ServicioRegistro`: CRUD completo con validación
- `ServicioEstadisticas`: promedio, mediana, std, tendencias, récords históricos
- `ServicioAlertas`: motor de reglas clínicas para 7 métricas
- `ServicioInsights`: 6 tipos de insights automáticos en lenguaje natural
- `ServicioExportacion`: PDF (ReportLab), CSV y Excel (openpyxl)
- `ServicioBackup`: copias de seguridad con rotación automática

#### Interfaz Gráfica
- Modo oscuro y claro con cambio en tiempo real sin reiniciar
- Sidebar de navegación con 7 módulos y badge de alertas
- Dashboard con 8 tarjetas de métricas con indicador de criticidad
- Tarjetas con tendencia (↑↓→) y porcentaje de cambio
- Formulario de registro con validación en tiempo real
- Cálculo de IMC visible mientras se escribe el peso
- Historial con calendario interactivo — días con datos resaltados
- Estadísticas con paneles individuales para 16 métricas
- Promedios semanales en gráfica de barras
- Récords históricos máximos y mínimos
- Panel de alertas con marcado automático como vistas
- Widget de ayuda con umbrales clínicos de referencia
- Configuración con perfil, objetivos, tema y backup

#### Gráficas
- Línea temporal con área rellena y promedio móvil (ventana 5d)
- Anotación automática del valor máximo
- Zonas de referencia clínica (verde/rojo)
- Gráfica de barras con promedios semanales y línea de media
- Todas las gráficas responden al cambio de tema

#### Scripts y Herramientas
- `scripts/seed_data.py`: genera 60 días de datos demo realistas
- `scripts/build_exe.py`: compila a EXE portable con PyInstaller
- Suite de tests con pytest (modelos y servicios)

#### Documentación
- README.md profesional con tabla de características
- DOCUMENTACION_TECNICA.md con arquitectura y esquema de BD
- API_INTERNA.md con referencia completa de todos los servicios
- GUIA_DESARROLLADOR.md con instrucciones para extender el sistema
- CHANGELOG.md y CONTRIBUTING.md
- `.gitignore` configurado para datos personales y archivos generados

---

## Próximas versiones planificadas

### [1.1.0] — Previsto Q3 2026
- Notificaciones del sistema (Windows Toast Notifications)
- Recordatorios configurables por período del día
- Gráfica de correlación entre métricas (ej. estrés vs presión)
- Heatmap de actividad mensual estilo GitHub

### [1.2.0] — Previsto Q4 2026
- Integración Bluetooth con glucómetros y tensiómetros
- Importación de datos desde archivos CSV externos
- Comparativa entre fechas seleccionadas manualmente

### [2.0.0] — Previsto 2027
- Modo multiusuario con perfiles separados
- Sincronización cloud opcional (cifrada)
- API REST local para integraciones externas
- Análisis predictivo con regresión lineal
