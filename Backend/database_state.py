"""Inspeccion de SOLO LECTURA del estado de la base SQLite.

Lo usan el runner de migraciones, el sistema de backups, la restauracion y el
endpoint de estado del sistema. Ninguna funcion de este modulo escribe en la
base: abren el archivo, leen y lo cierran.
"""

import os
import sqlite3


EXPECTED_TABLES = (
    "attributes",
    "categories",
    "product_attributes",
    "products",
    "sale_items",
    "sales",
)

VERSION_TABLE = "alembic_version"


class DatabaseInspectionError(RuntimeError):
    """El archivo existe pero no se puede leer como una base SQLite valida."""


def database_exists(db_path):
    return os.path.isfile(db_path)


def _connect(db_path):
    try:
        return sqlite3.connect(db_path)
    except sqlite3.DatabaseError as exc:
        raise DatabaseInspectionError(
            f"No se pudo abrir la base de datos '{db_path}': {exc}"
        ) from exc


def _query(db_path, sql, parameters=()):
    connection = _connect(db_path)
    try:
        return connection.execute(sql, parameters).fetchall()
    except sqlite3.DatabaseError as exc:
        raise DatabaseInspectionError(
            f"El archivo '{db_path}' no es una base SQLite legible: {exc}"
        ) from exc
    finally:
        connection.close()


def existing_tables(db_path):
    """Nombres de las tablas de usuario. Conjunto vacio si el archivo no existe."""
    if not database_exists(db_path):
        return set()

    rows = _query(db_path, "SELECT name FROM sqlite_master WHERE type = 'table'")
    return {row[0] for row in rows if not row[0].startswith("sqlite_")}


def has_expected_tables(db_path):
    """True si estan las 6 tablas del producto."""
    return set(EXPECTED_TABLES).issubset(existing_tables(db_path))


def has_data(db_path):
    """True si alguna de las 6 tablas del producto tiene al menos una fila."""
    if not database_exists(db_path):
        return False

    tables = existing_tables(db_path)
    for table in EXPECTED_TABLES:
        if table not in tables:
            continue
        rows = _query(db_path, f'SELECT COUNT(*) FROM "{table}"')
        if rows and rows[0][0] > 0:
            return True
    return False


def table_row_counts(db_path):
    """Conteo de filas por tabla del producto. Sirve para verificar adopciones."""
    counts = {}
    tables = existing_tables(db_path)
    for table in EXPECTED_TABLES:
        if table not in tables:
            counts[table] = None
            continue
        rows = _query(db_path, f'SELECT COUNT(*) FROM "{table}"')
        counts[table] = rows[0][0] if rows else 0
    return counts


def schema_revision(db_path):
    """Revision registrada en ``alembic_version``, o None si no esta versionada."""
    if not database_exists(db_path):
        return None

    tables = existing_tables(db_path)
    if VERSION_TABLE not in tables:
        return None

    rows = _query(db_path, f'SELECT version_num FROM "{VERSION_TABLE}" LIMIT 1')
    return rows[0][0] if rows else None
