"""
HealthTrack Pro — Punto de entrada principal.

Ejecuta: python main.py
"""

import sys
import os

# Asegurar que el directorio raíz esté en el path (necesario para PyInstaller)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.application import Application


def main() -> None:
    """Inicializa y ejecuta HealthTrack Pro."""
    aplicacion = Application()
    codigo_salida = aplicacion.ejecutar()
    sys.exit(codigo_salida)


if __name__ == "__main__":
    main()
