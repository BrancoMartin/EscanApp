"""Copias de seguridad locales de la base SQLite.

Reglas que implementa este modulo:

- La copia se hace con la API ``sqlite3.Connection.backup()``, no copiando el
  archivo a mano: SQLite garantiza una copia consistente aunque haya escrituras
  en curso.
- Cada copia se verifica abriendola, corriendo ``PRAGMA integrity_check`` y
  comprobando que esten las 6 tablas del producto. Si no pasa, se descarta.
- Nunca se sobrescribe una copia valida: el nombre lleva revision, fecha y un
  contador si hiciera falta.
- Se conservan las ultimas N copias (5 por defecto). N se configura con
  ``ESCANAPP_BACKUP_RETENTION``.
- Hay una copia automatica al arrancar como maximo cada N horas (24 por
  defecto, configurable con ``ESCANAPP_BACKUP_INTERVAL_HOURS``) y solo si la
  base tiene datos.
- Cada intento queda registrado en ``backups/manifest.json`` con fecha, version
  del producto, revision de esquema y resultado.
"""

import json
import os
import sqlite3
import time
from datetime import datetime

from Backend import database_state, runtime


MANIFEST_NAME = "manifest.json"
BACKUP_PREFIX = "pos-backup-"
PRERESTORE_PREFIX = "pos-prerestore-"
MANAGED_PREFIXES = (BACKUP_PREFIX, PRERESTORE_PREFIX)

DEFAULT_RETENTION = 5
DEFAULT_INTERVAL_HOURS = 24.0

ENV_RETENTION = "ESCANAPP_BACKUP_RETENTION"
ENV_INTERVAL = "ESCANAPP_BACKUP_INTERVAL_HOURS"


class BackupError(RuntimeError):
    """No se pudo crear o validar una copia de seguridad."""


def retention_limit():
    """Cuantas copias conservar. Valor invalido o ausente: 5."""
    raw = os.environ.get(ENV_RETENTION)
    if raw is None or raw.strip() == "":
        return DEFAULT_RETENTION
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_RETENTION
    return value if value > 0 else DEFAULT_RETENTION


def backup_interval_hours():
    """Cada cuantas horas se crea una copia automatica. Invalido: 24."""
    raw = os.environ.get(ENV_INTERVAL)
    if raw is None or raw.strip() == "":
        return DEFAULT_INTERVAL_HOURS
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_INTERVAL_HOURS
    return value if value > 0 else DEFAULT_INTERVAL_HOURS


def _backup_dir(backup_dir=None):
    path = backup_dir or runtime.backups_dir()
    os.makedirs(path, exist_ok=True)
    return path


def _timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _safe_revision(revision):
    if not revision:
        return "legacy"
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in str(revision)
    )
    return cleaned or "legacy"


def _unique_path(directory, prefix, revision):
    stem = f"{prefix}{_safe_revision(revision)}-{_timestamp()}"
    candidate = os.path.join(directory, f"{stem}.db")
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{stem}-{counter}.db")
        counter += 1
    return candidate


def verify_backup(path):
    """Abre la copia y comprueba que sea una base SQLite completa del producto.

    Devuelve ``(ok, detalle)``. No lanza: el detalle se registra en el manifiesto.
    """
    if not os.path.isfile(path):
        return False, "El archivo de copia no existe."

    try:
        connection = sqlite3.connect(path)
    except sqlite3.DatabaseError as exc:
        return False, f"No se pudo abrir la copia: {exc}"

    try:
        check = connection.execute("PRAGMA integrity_check").fetchone()
        if not check or check[0] != "ok":
            return False, f"integrity_check devolvio: {check[0] if check else 'sin resultado'}"

        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        tables = {row[0] for row in rows if not row[0].startswith("sqlite_")}
        missing = sorted(set(database_state.EXPECTED_TABLES) - tables)
        if missing:
            return False, "Faltan tablas en la copia: " + ", ".join(missing)
    except sqlite3.DatabaseError as exc:
        return False, f"La copia no se pudo leer: {exc}"
    finally:
        connection.close()

    return True, "ok"


# --------------------------------------------------------------------------- #
# Manifiesto
# --------------------------------------------------------------------------- #

def _manifest_path(backup_dir=None):
    return os.path.join(_backup_dir(backup_dir), MANIFEST_NAME)


def read_manifest(backup_dir=None):
    """Registros del manifiesto. Un manifiesto ausente o ilegible da lista vacia."""
    path = _manifest_path(backup_dir)
    if not os.path.isfile(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []

    entries = data.get("entries") if isinstance(data, dict) else None
    return entries if isinstance(entries, list) else []


def _write_manifest(entries, backup_dir=None):
    path = _manifest_path(backup_dir)
    temporary = path + ".tmp"
    payload = {"entries": entries}
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    os.replace(temporary, path)


def record_event(backup_dir=None, **fields):
    """Agrega un registro al manifiesto y devuelve el registro guardado."""
    record = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "app_version": runtime.version(),
        **fields,
    }
    entries = read_manifest(backup_dir)
    entries.append(record)
    _write_manifest(entries, backup_dir)
    return record


# --------------------------------------------------------------------------- #
# Listado y retencion
# --------------------------------------------------------------------------- #

def list_backups(backup_dir=None):
    """Copias administradas por EscanApp, de la mas nueva a la mas vieja."""
    directory = _backup_dir(backup_dir)
    entries = []

    for name in os.listdir(directory):
        if not name.endswith(".db"):
            continue
        if not name.startswith(MANAGED_PREFIXES):
            continue
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        stat = os.stat(path)
        entries.append(
            {
                "name": name,
                "path": path,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(
                    timespec="seconds"
                ),
                "mtime": stat.st_mtime,
                "kind": "prerestore" if name.startswith(PRERESTORE_PREFIX) else "backup",
            }
        )

    entries.sort(key=lambda item: item["mtime"], reverse=True)
    return entries


def prune_backups(backup_dir=None, keep=None):
    """Borra las copias mas viejas y conserva las ``keep`` mas recientes."""
    limit = keep if keep is not None else retention_limit()
    entries = list_backups(backup_dir)

    deleted = []
    for entry in entries[limit:]:
        try:
            os.remove(entry["path"])
            deleted.append(entry["path"])
        except OSError:
            # Un archivo que no se puede borrar no debe romper el arranque.
            continue
    return deleted


# --------------------------------------------------------------------------- #
# Creacion
# --------------------------------------------------------------------------- #

def create_backup(db_path=None, backup_dir=None, reason="manual", prefix=BACKUP_PREFIX):
    """Crea, verifica y registra una copia. Devuelve la ruta final.

    Si la copia no pasa la verificacion se elimina y se lanza ``BackupError``.
    """
    db_path = db_path or runtime.db_path()
    directory = _backup_dir(backup_dir)

    if not database_state.database_exists(db_path):
        raise BackupError("No hay base de datos para respaldar.")

    revision = database_state.schema_revision(db_path)
    final_path = _unique_path(directory, prefix, revision)
    temporary = final_path + ".tmp"

    source = None
    destination = None
    try:
        source = sqlite3.connect(db_path)
        destination = sqlite3.connect(temporary)
        source.backup(destination)
        destination.close()
        destination = None
        source.close()
        source = None

        os.replace(temporary, final_path)
    except (sqlite3.DatabaseError, OSError) as exc:
        if destination is not None:
            destination.close()
        if source is not None:
            source.close()
        for path in (temporary, final_path):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        record_event(
            directory,
            kind="backup",
            reason=reason,
            filename=None,
            revision=revision,
            result="failed",
            detail=str(exc),
        )
        raise BackupError(f"No se pudo crear la copia de seguridad: {exc}") from exc

    ok, detail = verify_backup(final_path)
    if not ok:
        try:
            os.remove(final_path)
        except OSError:
            pass
        record_event(
            directory,
            kind="backup",
            reason=reason,
            filename=None,
            revision=revision,
            result="failed",
            detail=detail,
        )
        raise BackupError(f"La copia de seguridad no es valida: {detail}")

    record_event(
        directory,
        kind="backup",
        reason=reason,
        filename=os.path.basename(final_path),
        revision=revision,
        size_bytes=os.path.getsize(final_path),
        result="ok",
        detail=detail,
    )
    prune_backups(directory)
    return final_path


def maybe_scheduled_backup(db_path=None, backup_dir=None):
    """Copia automatica de arranque, respetando el intervalo configurado.

    No hace nada si la base no existe, esta vacia o la ultima copia es mas nueva
    que el intervalo. Devuelve la ruta creada o None.
    """
    db_path = db_path or runtime.db_path()

    if not database_state.database_exists(db_path):
        return None
    if not database_state.has_data(db_path):
        return None

    interval_seconds = backup_interval_hours() * 3600.0
    entries = list_backups(backup_dir)
    if entries:
        newest = entries[0]["mtime"]
        if time.time() - newest < interval_seconds:
            return None

    return create_backup(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="scheduled",
        prefix=BACKUP_PREFIX,
    )
