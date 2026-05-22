"""
Script de datos demo para HealthTrack Pro.

Genera 60 días de registros de salud simulados con variaciones
realistas para demostrar todas las funcionalidades de la app.

Uso:
    python scripts/seed_data.py
"""

import sys
import os
import random
from datetime import date, timedelta

# Agregar el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def generar_valor_realista(base: float, variacion: float, tendencia: float = 0) -> float:
    """Genera un valor con distribución normal alrededor de la base."""
    return round(base + random.gauss(0, variacion) + tendencia, 1)


def main():
    from database.connection import obtener_gestor
    from services.registro_service import ServicioRegistro
    from services.alertas_service import ServicioAlertas
    from core.constants import PERIODOS_LISTA

    print("=" * 60)
    print("  HealthTrack Pro — Generador de Datos Demo")
    print("=" * 60)

    gestor = obtener_gestor()
    servicio = ServicioRegistro()
    servicio_alertas = ServicioAlertas()

    hoy = date.today()
    dias_demo = 60
    registros_creados = 0

    for dias_atras in range(dias_demo, 0, -1):
        fecha = hoy - timedelta(days=dias_atras)

        # Calcular tendencia gradual (simula mejora de salud)
        factor_tiempo = (dias_demo - dias_atras) / dias_demo
        # La presión mejora ligeramente con el tiempo
        tendencia_presion = -5 * factor_tiempo

        # Probabilidad de registrar según el día (más los recientes)
        prob_registro = 0.5 + 0.4 * factor_tiempo

        # Seleccionar períodos aleatoriamente
        periodos_disponibles = PERIODOS_LISTA.copy()
        num_periodos = random.choices([1, 2, 3], weights=[0.3, 0.4, 0.3])[0]
        periodos_del_dia = random.sample(periodos_disponibles, min(num_periodos, 3))

        for periodo in periodos_del_dia:
            if random.random() > prob_registro:
                continue

            datos = {
                "fecha": fecha,
                "periodo": periodo,
                # Cardiovascular
                "presion_sistolica": int(generar_valor_realista(
                    130 + tendencia_presion, 12
                )),
                "presion_diastolica": int(generar_valor_realista(
                    83 + (tendencia_presion * 0.6), 8
                )),
                "ritmo_cardiaco": int(generar_valor_realista(72, 10)),
                "oxigenacion": round(generar_valor_realista(97.5, 1.2), 1),
                # Física
                "peso": round(generar_valor_realista(78.5 - 3 * factor_tiempo, 0.5), 1),
                "pasos": int(generar_valor_realista(7500 + 1000 * factor_tiempo, 2000)),
                "distancia_caminada": round(generar_valor_realista(5.2, 1.5), 1),
                "calorias_quemadas": int(generar_valor_realista(2100, 300)),
                # Descanso (solo para período noche)
                "horas_sueno": round(generar_valor_realista(7.0, 1.0), 1) if periodo == "noche" else None,
                "calidad_sueno": random.randint(5, 9) if periodo == "noche" else None,
                # Mental
                "nivel_estres": random.randint(2, 8),
                "estado_animo": random.randint(5, 9),
                # Opcionales (no siempre registrados)
                "glucosa": round(generar_valor_realista(95, 10), 1) if random.random() > 0.5 else None,
                "temperatura_corporal": round(generar_valor_realista(36.6, 0.3), 1) if random.random() > 0.7 else None,
                "consumo_agua": round(generar_valor_realista(2.0, 0.5), 1) if random.random() > 0.4 else None,
                "cafeina": random.choice([0, 80, 100, 150, 200]) if random.random() > 0.5 else None,
            }

            # Asegurar rangos válidos
            datos["presion_sistolica"] = max(90, min(185, datos["presion_sistolica"]))
            datos["presion_diastolica"] = max(55, min(130, datos["presion_diastolica"]))
            datos["ritmo_cardiaco"] = max(50, min(130, datos["ritmo_cardiaco"]))
            datos["oxigenacion"] = max(90.0, min(100.0, datos["oxigenacion"]))
            datos["peso"] = max(60.0, min(120.0, datos["peso"]))
            if datos["horas_sueno"]:
                datos["horas_sueno"] = max(3.0, min(12.0, datos["horas_sueno"]))

            # Agregar notas médicas esporádicamente
            if random.random() > 0.8:
                datos["notas_medicas"] = random.choice([
                    "Visita médica rutinaria — todo normal",
                    "Ligero dolor de cabeza por la tarde",
                    "Empecé nueva rutina de ejercicio",
                    "Reducción de sal en la dieta",
                    "Control de glucosa — resultados normales",
                ])

            try:
                registro, creado = servicio.guardar_o_actualizar(datos)
                if creado:
                    registros_creados += 1
                    # Generar alertas para el registro
                    try:
                        servicio_alertas.evaluar_registro(registro)
                    except Exception:
                        pass
            except Exception as e:
                print(f"  ⚠ Error en {fecha} {periodo}: {e}")

        if dias_atras % 10 == 0:
            print(f"  Procesando... {dias_demo - dias_atras}/{dias_demo} dias")

    print(f"\n  [OK] Datos demo generados: {registros_creados} registros")
    print(f"  [OK] Periodo: {hoy - timedelta(days=dias_demo)} al {hoy}")
    print("\nEjecuta la app con: python main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
