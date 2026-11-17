"""Restauracion de una copia de seguridad sobre la base activa.

La restauracion es una operacion de mantenimiento, no una operacion de venta:
exige que la aplicacion NO este usando la base. Antes de reemplazar nada:

1. valida que la copia elegida se pueda abrir y tenga las 6 tablas;
2. toma el lock exclusivo de la base (la app lo retiene mientras vive);
3. guarda una copia verificada de la base ACTUAL (``pos-prerestore-*``), que es
   el camino de vuelta si la restauracion falla a mitad de camino.

Recien despues copia la elegida sobre ``pos.db`` con la API de backup de SQLite
y verifica el resultado. Cualquier error deja el estado anterior disponible.
"""

import os
import sqlite3

from Backend import database_backup, database_state, runtime
from Backend.db_lock import DatabaseLock, lock_path_for


class RestoreError(RuntimeError):
    """La restauracion no se pudo completar y se informa el estado."""


class RestoreBlockedError(RestoreError):
    """Hay operaciones activas sobre la base; no se restaura."""


def _copy_database(source_path, destination_path):
    source = sqlite3.connect(source_path)
    destination = sqlite3.connect(destination_path)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()


def _remove_sidecars(db_path):
    for suffix in ("-wal", "-shm", "-journal"):
        path = db_path + suffix
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def restore_backup(backup_path, db_path=None, backup_dir=None):
    """Restaura ``backup_path`` sobre la base indicada.

    Devuelve un resumen con la copia usada y la copia de seguridad de la base
    anterior. Lanza ``RestoreBlockedError`` si hay otro proceso usando la base y
    ``RestoreError`` si la copia es invalida o la operacion falla.
    """
    db_path = db_path or runtime.db_path()
    backup_path = os.path.abspath(backup_path)

    if not os.path.isfile(backup_path):
        raise RestoreError(f"No existe la copia de seguridad: {backup_path}")

    ok, detail = database_backup.verify_backup(backup_path)
    if not ok:
        raise RestoreError(
            f"La copia elegida no es valida y no se restauro nada: {detail}"
        )

    lock = DatabaseLock(lock_path_for(db_path))
    if not lock.acquire(blocking=False):
        raise RestoreBlockedError(
            "No se puede restaurar mientras EscanApp esta abierta o hay otra "
            "restauracion en curso. Cerra la aplicacion y volve a intentarlo."
        )

    safety_path = None
    try:
        if database_state.database_exists(db_path):
            safety_path = database_backup.create_backup(
                db_path=db_path,
                backup_dir=backup_dir,
                reason="pre-restore",
                prefix=database_backup.PRERESTORE_PREFIX,
            )

        try:
            _copy_database(backup_path, db_path)
            _remove_sidecars(db_path)
        except (sqlite3.DatabaseError, OSError) as exc:
            raise RestoreError(
                "No se pudo escribir la copia sobre la base actual. "
                + (
                    f"La base anterior quedo guardada en: {safety_path}."
                    if safety_path
                    else "No habia una base anterior para proteger."
                )
                + f" Detalle tecnico: {exc}"
            ) from exc

        restored_ok, restored_detail = database_backup.verify_backup(db_path)
        if not restored_ok:
            if safety_path:
                try:
                    _copy_database(safety_path, db_path)
                    _remove_sidecars(db_path)
                except (sqlite3.DatabaseError, OSError):
                    pass
            raise RestoreError(
                "La copia se escribio pero no quedo una base valida. "
                + (
                    f"Se intento volver a la base anterior, guardada en: {safety_path}."
                    if safety_path
                    else "No habia una base anterior para volver."
                )
                + f" Detalle tecnico: {restored_detail}"
            )

        revision = database_state.schema_revision(db_path)
        database_backup.record_event(
            backup_dir,
            kind="restore",
            filename=os.path.basename(backup_path),
            revision=revision,
            result="ok",
            detail=(
                f"Copia de seguridad previa: {safety_path}"
                if safety_path
                else "No habia base anterior"
            ),
        )
        return {
            "restored_from": backup_path,
            "safety_backup": safety_path,
            "schema_revision": revision,
        }
    finally:
        lock.release()
