"""Restauracion: reemplazo seguro, copia previa y rechazos."""

import hashlib
import os
import sqlite3

import pytest

from Backend import database_backup
from Backend.database_restore import RestoreBlockedError, RestoreError, restore_backup
from Backend.db_lock import DatabaseLock, lock_path_for


def _sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _insert_product(db_path, name, barcode):
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "INSERT INTO products (name, price, barcode) VALUES (?, 100.0, ?)",
            (name, barcode),
        )
        connection.commit()
    finally:
        connection.close()


def _product_names(db_path):
    connection = sqlite3.connect(db_path)
    try:
        return [row[0] for row in connection.execute("SELECT name FROM products")]
    finally:
        connection.close()


def test_restore_returns_to_the_backed_up_state(db_path, backup_dir):
    _insert_product(db_path, "original", "7790300")
    backup = database_backup.create_backup(db_path=db_path, backup_dir=backup_dir)

    _insert_product(db_path, "posterior", "7790301")
    assert _product_names(db_path) == ["original", "posterior"]

    result = restore_backup(backup, db_path=db_path, backup_dir=backup_dir)

    assert _product_names(db_path) == ["original"]
    assert result["restored_from"] == backup
    assert result["safety_backup"] is not None
    assert os.path.isfile(result["safety_backup"])


def test_restore_keeps_the_previous_database_as_safety_copy(db_path, backup_dir):
    _insert_product(db_path, "original", "7790302")
    backup = database_backup.create_backup(db_path=db_path, backup_dir=backup_dir)

    _insert_product(db_path, "posterior", "7790303")
    result = restore_backup(backup, db_path=db_path, backup_dir=backup_dir)

    assert "posterior" in _product_names(result["safety_backup"])
    ok, _ = database_backup.verify_backup(result["safety_backup"])
    assert ok is True

    entries = database_backup.read_manifest(backup_dir)
    assert entries[-1]["kind"] == "restore"
    assert entries[-1]["result"] == "ok"


def test_restore_rejects_invalid_backup_without_touching_database(
    db_path, backup_dir, tmp_path
):
    _insert_product(db_path, "intacto", "7790304")
    before = _sha256(db_path)

    invalid = tmp_path / "invalida.db"
    invalid.write_bytes(b"esto no es una base sqlite")

    with pytest.raises(RestoreError, match="no es valida"):
        restore_backup(str(invalid), db_path=db_path, backup_dir=backup_dir)

    assert _sha256(db_path) == before
    assert _product_names(db_path) == ["intacto"]


def test_restore_of_missing_backup_fails(db_path, backup_dir, tmp_path):
    with pytest.raises(RestoreError, match="No existe la copia"):
        restore_backup(
            str(tmp_path / "no-existe.db"), db_path=db_path, backup_dir=backup_dir
        )


def test_restore_is_blocked_while_the_database_is_in_use(db_path, backup_dir):
    _insert_product(db_path, "original", "7790305")
    backup = database_backup.create_backup(db_path=db_path, backup_dir=backup_dir)

    lock = DatabaseLock(lock_path_for(db_path))
    assert lock.acquire() is True
    try:
        with pytest.raises(RestoreBlockedError, match="EscanApp esta abierta"):
            restore_backup(backup, db_path=db_path, backup_dir=backup_dir)
    finally:
        lock.release()

    # Sin lock, la misma restauracion procede.
    result = restore_backup(backup, db_path=db_path, backup_dir=backup_dir)
    assert result["schema_revision"] is not None
