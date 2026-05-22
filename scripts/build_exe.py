"""
Script de compilación a EXE con PyInstaller.

Genera un ejecutable portable de HealthTrack Pro para Windows.

Uso:
    python scripts/build_exe.py
"""

import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def compilar() -> None:
    print("=" * 60)
    print("  HealthTrack Pro — Compilación EXE")
    print("=" * 60)

    # Verificar PyInstaller
    try:
        import PyInstaller
        print(f"  PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("  ✕ PyInstaller no encontrado. Instalar con: pip install pyinstaller")
        sys.exit(1)

    # Directorio de salida
    dist_dir = BASE_DIR / "dist"
    build_dir = BASE_DIR / "build"
    spec_dir = BASE_DIR / "build"

    comando = [
        sys.executable, "-m", "PyInstaller",
        "--name=HealthTrackPro",
        "--onefile",
        "--windowed",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={spec_dir}",
        "--add-data=config;config",
        "--add-data=assets;assets",
        "--hidden-import=sqlalchemy.dialects.sqlite",
        "--hidden-import=matplotlib.backends.backend_qtagg",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--collect-all=matplotlib",
        "--collect-all=numpy",
        str(BASE_DIR / "main.py"),
    ]

    print("\n  Ejecutando PyInstaller...")
    print(f"  Destino: {dist_dir}")

    resultado = subprocess.run(comando, cwd=str(BASE_DIR))

    if resultado.returncode == 0:
        exe_ruta = dist_dir / "HealthTrackPro.exe"
        if exe_ruta.exists():
            tamanio_mb = exe_ruta.stat().st_size / (1024 * 1024)
            print(f"\n  ✓ Compilación exitosa")
            print(f"  ✓ Ejecutable: {exe_ruta}")
            print(f"  ✓ Tamaño: {tamanio_mb:.1f} MB")
        else:
            print(f"\n  ✓ Compilación completada en: {dist_dir}")
    else:
        print("\n  ✕ Error durante la compilación")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    compilar()
