"""Aplicacion automatica de las migraciones de Alembic al arrancar.

La clasificacion de la base es la decision central:

| Caso | Estado detectado                                        | Accion                   |
|------|---------------------------------------------------------|--------------------------|
| A    | el archivo no existe                                    | upgrade head             |
| B    | existe y tiene ``alembic_version``                      | upgrade head (no-op si al dia) |
| C    | existe, sin version, con las 6 tablas del producto      | stamp base + upgrade head |
| D    | existe, sin version, sin ninguna tabla                  | upgrade head             |
| E    | existe, sin version, con tablas pero sin las 6 esperadas | abortar sin escribir    |

El caso C es una base 1.0.x de un cliente: se sella en la revision base en vez
de intentar recrear tablas que ya existen. El caso E es una base desconocida:
el sistema no adivina, se niega a operar y lo informa.

Antes de aplicar cambios sobre una base con datos se crea una copia verificada
(``Backend.database_backup``); si la copia falla, NO se migra.
"""

import os

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from Backend import database_backup, database_state, runtime
from Backend.db_lock import acquire_runtime_lock


CASE_NEW = "A"
CASE_VERSIONED = "B"
CASE_LEGACY = "C"
CASE_EMPTY = "D"
CASE_UNKNOWN = "E"


class MigrationError(RuntimeError):
    """La base no se puede migrar de forma segura. La base queda intacta."""


def _build_config(db_path):
    config = Config()
    # En runtime no se lee alembic.ini: script_location y url van en memoria.
    config.set_main_option("script_location", runtime.migrations_dir())
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def _script(config):
    return ScriptDirectory.from_config(config)


def classify(db_path):
    """Devuelve el caso A-E para el archivo indicado. Nunca lo modifica."""
    if not database_state.database_exists(db_path):
        return CASE_NEW

    try:
        tables = database_state.existing_tables(db_path)
    except database_state.DatabaseInspectionError:
        # El archivo existe pero no es SQLite: es tan desconocido como el caso E
        # y no se debe tocar.
        return CASE_UNKNOWN

    if database_state.VERSION_TABLE in tables:
        return CASE_VERSIONED
    if not tables:
        return CASE_EMPTY
    if set(database_state.EXPECTED_TABLES).issubset(tables):
        return CASE_LEGACY
    return CASE_UNKNOWN


def current_revision(db_path):
    """Revision registrada en la base, o None si no esta versionada."""
    return database_state.schema_revision(db_path)


def head_revision():
    """Ultima revision disponible en los scripts de migracion."""
    return _script(_build_config(runtime.db_path())).get_current_head()


def schema_status(db_path=None):
    """Estado de esquema para diagnostico. Nunca lanza."""
    db_path = db_path or runtime.db_path()
    try:
        current = current_revision(db_path)
        head = _script(_build_config(db_path)).get_current_head()
        return {
            "schema_revision": current,
            "schema_is_head": current is not None and current == head,
        }
    except Exception:
        return {"schema_revision": None, "schema_is_head": False}


def _unknown_database_error(db_path):
    return MigrationError(
        "La base de datos de EscanApp no se reconoce y no se va a modificar. "
        f"Archivo: {db_path}. "
        "No tiene el registro de version del esquema ni las tablas esperadas del "
        "producto. Tus datos NO fueron tocados. Contacta a soporte con esta ruta."
    )


def _classify_or_raise(db_path):
    case = classify(db_path)
    if case == CASE_UNKNOWN:
        raise _unknown_database_error(db_path)
    return case


def _plan(case, db_path, script):
    """Revisa el estado y devuelve (head, base, current, hay_cambios)."""
    head = script.get_current_head()
    base_revision = script.get_base()
    # Segun la version de Alembic, get_base() devuelve el id o el Script.
    base = getattr(base_revision, "revision", base_revision)

    current = None
    if case == CASE_VERSIONED:
        current = database_state.schema_revision(db_path)
        known = script.get_revision(current) if current else None
        if known is None:
            raise MigrationError(
                f"La base de datos esta en la revision '{current}', que esta "
                "aplicacion no conoce. Es probable que haya sido abierta por una "
                "version mas nueva de EscanApp. No se tocaron los datos. "
                "Reinstala la version correspondiente o contacta a soporte."
            )

    if case in (CASE_NEW, CASE_EMPTY, CASE_LEGACY):
        has_changes = head is not None
    else:
        has_changes = current != head

    return head, base, current, has_changes


def run_migrations(db_path=None, backup_dir=None, log=print):
    """Clasifica, respalda si hace falta y aplica las migraciones pendientes.

    Devuelve un resumen. Si algo falla lanza ``MigrationError``; en el caso A
    (archivo inexistente) el archivo a medio crear se elimina, porque nunca tuvo
    datos. En los demas casos la base queda en la revision anterior (cada
    revision corre en su propia transaccion y existe la copia previa).
    """
    db_path = db_path or runtime.db_path()
    case = _classify_or_raise(db_path)

    config = _build_config(db_path)
    script = _script(config)
    head, base, current, has_changes = _plan(case, db_path, script)

    existed_before = database_state.database_exists(db_path)
    backup_path = None

    if has_changes and case in (CASE_LEGACY, CASE_VERSIONED):
        if database_state.has_data(db_path):
            backup_path = database_backup.create_backup(
                db_path=db_path,
                backup_dir=backup_dir,
                reason="pre-migration",
            )
            log(f"[MIGRATIONS] Copia de seguridad previa: {backup_path}")

    if not has_changes:
        log(
            "[MIGRATIONS] Sin cambios: la base ya esta en la ultima revision "
            f"({head})."
        )
        return {
            "case": case,
            "previous_revision": current,
            "revision": current,
            "head": head,
            "backup": None,
            "applied": False,
        }

    log(
        f"[MIGRATIONS] Caso {case}: aplicando migraciones "
        f"({current or 'sin version'} -> {head})."
    )

    try:
        if case == CASE_LEGACY:
            # Sellar: la base ya tiene el esquema de la revision base. Ejecutar
            # la revision fallaria con "table ... already exists".
            log(f"[MIGRATIONS] Base 1.0.x detectada: sellando en {base}.")
            command.stamp(config, base)
            command.upgrade(config, "head")
        else:
            command.upgrade(config, "head")
    except MigrationError:
        raise
    except Exception as exc:
        if not existed_before and database_state.database_exists(db_path):
            # El archivo lo creamos nosotros en este arranque y nunca tuvo datos.
            try:
                os.remove(db_path)
            except OSError:
                pass
        detalle_copia = (
            f" Se conserva la copia previa en: {backup_path}." if backup_path else ""
        )
        raise MigrationError(
            "No se pudo actualizar la base de datos de EscanApp. "
            "Tus datos estan intactos y la aplicacion no va a arrancar hasta "
            f"resolverlo.{detalle_copia} Detalle tecnico: {exc}"
        ) from exc

    revision = database_state.schema_revision(db_path)
    if revision != head:
        raise MigrationError(
            "La migracion termino pero la base no quedo en la ultima revision "
            f"(esperada {head}, obtenida {revision}). No sigas operando: "
            "contacta a soporte."
        )

    log(f"[MIGRATIONS] Base actualizada a {revision}.")
    return {
        "case": case,
        "previous_revision": current,
        "revision": revision,
        "head": head,
        "backup": backup_path,
        "applied": True,
    }


def run_startup_migrations(db_path=None, backup_dir=None, log=print):
    """Arranque de la aplicacion: lock, migraciones y copia automatica."""
    db_path = db_path or runtime.db_path()

    # La app queda duena del lock mientras viva: una restauracion no puede
    # reemplazar la base por debajo.
    acquire_runtime_lock(db_path)

    report = run_migrations(db_path=db_path, backup_dir=backup_dir, log=log)

    scheduled = None
    try:
        scheduled = database_backup.maybe_scheduled_backup(
            db_path=db_path, backup_dir=backup_dir
        )
    except database_backup.BackupError as exc:
        # Una copia automatica fallida no debe impedir vender.
        log(f"[BACKUP] No se pudo crear la copia automatica: {exc}")

    if scheduled:
        log(f"[BACKUP] Copia automatica: {scheduled}")

    status = database_state.schema_revision(db_path)
    log(f"[DB] Revision de esquema: {status} (head: {report['head']})")

    report["scheduled_backup"] = scheduled
    return report
