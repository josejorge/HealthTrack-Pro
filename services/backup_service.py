"""
Servicio de backups automáticos de la base de datos SQLite.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from core.config import config
from core.exceptions import BackupError

logger = logging.getLogger("healthtrack.services.backup")


class ServicioBackup:
    """Gestiona la creación y rotación de backups de la base de datos."""

    def __init__(self) -> None:
        self._directorio = config.backup_directorio
        self._directorio.mkdir(parents=True, exist_ok=True)
        self._max_copias = config.obtener("backup_max_copias", 10)

    def crear_backup(self) -> Path:
        """
        Crea una copia de la base de datos con timestamp en el nombre.

        Returns:
            Ruta al archivo de backup creado.

        Raises:
            BackupError: Si la base de datos no existe o no se puede copiar.
        """
        ruta_db = config.db_ruta

        if not ruta_db.exists():
            raise BackupError("La base de datos no existe. Crea al menos un registro primero.")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_backup = f"healthtrack_backup_{ts}.db"
        ruta_backup = self._directorio / nombre_backup

        try:
            shutil.copy2(ruta_db, ruta_backup)
            logger.info("Backup creado: %s", ruta_backup)
            self._rotar_backups()
            return ruta_backup

        except OSError as e:
            raise BackupError(f"Error al crear backup: {e}") from e

    def listar_backups(self) -> list[Path]:
        """Devuelve lista de backups existentes, ordenados del más reciente al más antiguo."""
        backups = sorted(
            self._directorio.glob("healthtrack_backup_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return backups

    def restaurar_backup(self, ruta_backup: Path) -> None:
        """
        Restaura la base de datos desde un archivo de backup.

        ¡PELIGROSO! Sobrescribe la base de datos actual.
        """
        if not ruta_backup.exists():
            raise BackupError(f"El archivo de backup no existe: {ruta_backup}")

        # Primero hacemos backup del estado actual
        try:
            self.crear_backup()
        except BackupError:
            pass  # Si no hay DB actual, continuar igual

        try:
            shutil.copy2(ruta_backup, config.db_ruta)
            logger.info("Base de datos restaurada desde: %s", ruta_backup)
        except OSError as e:
            raise BackupError(f"Error al restaurar: {e}") from e

    def _rotar_backups(self) -> None:
        """Elimina los backups más antiguos si se supera el máximo configurado."""
        backups = self.listar_backups()
        exceso = len(backups) - self._max_copias

        for backup_antiguo in backups[self._max_copias:]:
            try:
                backup_antiguo.unlink()
                logger.debug("Backup antiguo eliminado: %s", backup_antiguo)
            except OSError as e:
                logger.warning("No se pudo eliminar backup: %s — %s", backup_antiguo, e)
