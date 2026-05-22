"""
Constantes globales de HealthTrack Pro.

Define umbrales de salud, colores, metadatos de la aplicación
y toda configuración inmutable del sistema.
"""

# ──────────────────────────────────────────────
# Metadatos de la aplicación
# ──────────────────────────────────────────────
APP_NOMBRE = "HealthTrack Pro"
APP_VERSION = "1.0.0"
APP_AUTOR = "HealthTrack Team"
APP_DESCRIPCION = "Seguimiento profesional de métricas de salud personal"
APP_SITIO_WEB = "https://healthtrackpro.app"
APP_SOPORTE = "soporte@healthtrackpro.app"

# ──────────────────────────────────────────────
# Periodos del día
# ──────────────────────────────────────────────
PERIODOS = {
    "manana": "Mañana",
    "tarde": "Tarde",
    "noche": "Noche",
}
PERIODOS_LISTA = list(PERIODOS.keys())
PERIODOS_DISPLAY = list(PERIODOS.values())

# ──────────────────────────────────────────────
# Niveles de criticidad
# ──────────────────────────────────────────────
CRITICIDAD_NORMAL = "normal"
CRITICIDAD_ATENCION = "atencion"
CRITICIDAD_PREOCUPANTE = "preocupante"
CRITICIDAD_CRITICO = "critico"

CRITICIDAD_LABELS = {
    CRITICIDAD_NORMAL: "Normal",
    CRITICIDAD_ATENCION: "Atención",
    CRITICIDAD_PREOCUPANTE: "Preocupante",
    CRITICIDAD_CRITICO: "Crítico",
}

# ──────────────────────────────────────────────
# Colores por criticidad (hex)
# ──────────────────────────────────────────────
COLORES_CRITICIDAD = {
    CRITICIDAD_NORMAL: "#22c55e",
    CRITICIDAD_ATENCION: "#f59e0b",
    CRITICIDAD_PREOCUPANTE: "#f97316",
    CRITICIDAD_CRITICO: "#ef4444",
}

# Paleta de la UI — Modo Oscuro
COLORES_OSCURO = {
    "fondo_principal": "#0f172a",
    "fondo_secundario": "#1e293b",
    "fondo_tarjeta": "#1e293b",
    "fondo_input": "#0f172a",
    "borde": "#334155",
    "borde_focus": "#6366f1",
    "texto_primario": "#f1f5f9",
    "texto_secundario": "#94a3b8",
    "texto_deshabilitado": "#475569",
    "acento": "#6366f1",
    "acento_hover": "#4f46e5",
    "acento_pressed": "#4338ca",
    "sidebar_fondo": "#0f172a",
    "sidebar_item_hover": "#1e293b",
    "sidebar_item_activo": "#6366f1",
    "separador": "#1e293b",
    "scrollbar": "#334155",
    "scrollbar_hover": "#475569",
    "normal": "#22c55e",
    "atencion": "#f59e0b",
    "preocupante": "#f97316",
    "critico": "#ef4444",
    "grafica_fondo": "#1e293b",
    "grafica_grid": "#334155",
}

# Paleta de la UI — Modo Claro
COLORES_CLARO = {
    "fondo_principal": "#f8fafc",
    "fondo_secundario": "#ffffff",
    "fondo_tarjeta": "#ffffff",
    "fondo_input": "#f8fafc",
    "borde": "#e2e8f0",
    "borde_focus": "#6366f1",
    "texto_primario": "#0f172a",
    "texto_secundario": "#64748b",
    "texto_deshabilitado": "#94a3b8",
    "acento": "#6366f1",
    "acento_hover": "#4f46e5",
    "acento_pressed": "#4338ca",
    "sidebar_fondo": "#1e293b",
    "sidebar_item_hover": "#334155",
    "sidebar_item_activo": "#6366f1",
    "separador": "#e2e8f0",
    "scrollbar": "#cbd5e1",
    "scrollbar_hover": "#94a3b8",
    "normal": "#16a34a",
    "atencion": "#d97706",
    "preocupante": "#ea580c",
    "critico": "#dc2626",
    "grafica_fondo": "#ffffff",
    "grafica_grid": "#f1f5f9",
}

# ──────────────────────────────────────────────
# Umbrales clínicos — Presión arterial (mmHg)
# ──────────────────────────────────────────────
PRESION_SISTOLICA = {
    "normal_max": 119,
    "elevada_min": 120,
    "elevada_max": 129,
    "alta_1_min": 130,
    "alta_1_max": 139,
    "alta_2_min": 140,
    "crisis_min": 180,
}

PRESION_DIASTOLICA = {
    "normal_max": 79,
    "alta_1_min": 80,
    "alta_1_max": 89,
    "alta_2_min": 90,
    "crisis_min": 120,
}

# ──────────────────────────────────────────────
# Umbrales clínicos — Ritmo cardíaco (bpm)
# ──────────────────────────────────────────────
RITMO_CARDIACO = {
    "bradicardia_max": 59,
    "normal_min": 60,
    "normal_max": 100,
    "taquicardia_min": 101,
    "critico_min": 150,
}

# ──────────────────────────────────────────────
# Umbrales clínicos — Oxigenación SpO2 (%)
# ──────────────────────────────────────────────
OXIGENACION = {
    "normal_min": 95,
    "baja_min": 90,
    "critica_max": 89,
}

# ──────────────────────────────────────────────
# Umbrales — IMC (kg/m²)
# ──────────────────────────────────────────────
IMC = {
    "bajo_peso_max": 18.4,
    "normal_min": 18.5,
    "normal_max": 24.9,
    "sobrepeso_min": 25.0,
    "sobrepeso_max": 29.9,
    "obesidad_min": 30.0,
}

# ──────────────────────────────────────────────
# Umbrales — Glucosa en sangre (mg/dL)
# ──────────────────────────────────────────────
GLUCOSA = {
    "hipoglucemia_max": 69,
    "normal_min": 70,
    "normal_max": 99,
    "prediabetes_min": 100,
    "prediabetes_max": 125,
    "diabetes_min": 126,
}

# ──────────────────────────────────────────────
# Umbrales — Temperatura corporal (°C)
# ──────────────────────────────────────────────
TEMPERATURA = {
    "hipotermia_max": 35.9,
    "normal_min": 36.0,
    "normal_max": 37.2,
    "subfebril_min": 37.3,
    "subfebril_max": 37.9,
    "fiebre_min": 38.0,
    "fiebre_alta_min": 39.0,
    "critica_min": 40.0,
}

# ──────────────────────────────────────────────
# Umbrales — Sueño (horas)
# ──────────────────────────────────────────────
SUENO = {
    "insuficiente_max": 5.9,
    "recomendado_min": 7.0,
    "recomendado_max": 9.0,
    "excesivo_min": 9.1,
}

# ──────────────────────────────────────────────
# Umbrales — Pasos diarios
# ──────────────────────────────────────────────
PASOS = {
    "sedentario_max": 4999,
    "poco_activo_min": 5000,
    "poco_activo_max": 7499,
    "activo_min": 7500,
    "activo_max": 9999,
    "muy_activo_min": 10000,
}

# ──────────────────────────────────────────────
# Escalas subjetivas (1–10)
# ──────────────────────────────────────────────
ESCALA_ESTRES = {
    "bajo_max": 3,
    "moderado_min": 4,
    "moderado_max": 6,
    "alto_min": 7,
    "muy_alto_min": 9,
}

ESCALA_ANIMO = {
    "muy_bajo_max": 3,
    "bajo_min": 4,
    "bajo_max": 5,
    "normal_min": 6,
    "normal_max": 7,
    "bueno_min": 8,
}

ESCALA_CALIDAD_SUENO = {
    "muy_malo_max": 3,
    "malo_min": 4,
    "malo_max": 5,
    "regular_min": 6,
    "regular_max": 7,
    "bueno_min": 8,
}

# ──────────────────────────────────────────────
# Configuración de gráficas
# ──────────────────────────────────────────────
GRAFICA_COLORES_SERIES = [
    "#6366f1", "#22c55e", "#f59e0b", "#ef4444",
    "#3b82f6", "#a855f7", "#ec4899", "#14b8a6",
]

GRAFICA_PERIODOS_DISPLAY = {
    "7d": "Últimos 7 días",
    "30d": "Últimos 30 días",
    "90d": "Últimos 3 meses",
    "180d": "Últimos 6 meses",
    "365d": "Último año",
    "todo": "Todo el historial",
}

# ──────────────────────────────────────────────
# Configuración de exportación
# ──────────────────────────────────────────────
FORMATOS_EXPORTACION = ["PDF", "CSV", "Excel"]

# ──────────────────────────────────────────────
# Configuración de backup
# ──────────────────────────────────────────────
BACKUP_INTERVALO_DIAS = 7
BACKUP_MAX_COPIAS = 10

# ──────────────────────────────────────────────
# Dimensiones de la ventana
# ──────────────────────────────────────────────
VENTANA_ANCHO_MIN = 1200
VENTANA_ALTO_MIN = 700
VENTANA_ANCHO_DEFAULT = 1440
VENTANA_ALTO_DEFAULT = 900
SIDEBAR_ANCHO = 230

# ──────────────────────────────────────────────
# Iconos Unicode (emoji para botones y UI)
# ──────────────────────────────────────────────
ICONOS = {
    "dashboard": "⊞",
    "registro": "✚",
    "historial": "📅",
    "estadisticas": "📊",
    "alertas": "🔔",
    "configuracion": "⚙",
    "ayuda": "?",
    "exportar": "↗",
    "normal": "✓",
    "atencion": "⚠",
    "critico": "✕",
    "tendencia_sube": "↑",
    "tendencia_baja": "↓",
    "tendencia_estable": "→",
    "record_max": "▲",
    "record_min": "▼",
}
