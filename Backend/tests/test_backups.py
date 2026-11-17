"""Copias de seguridad: consistencia, verificacion, manifiesto y retencion."""

import os
import sqlite3
import time

import pytest

from Backend import database_backup
from Backend.database_backup import BackupError


def _insert_product(db_path, name="producto", barcode="7790200", price=100.0):
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "INSERT INTO products (name, price, barcode) VALUES (?, ?, ?)",
            (name, price, barcode),
        )
        connection.commit()
    finally:
        connection.close()


def test_backup_is_readable_and_registered(db_path, backup_dir):
    path = database_backup.create_backup(
        db_path=db_path, backup_dir=backup_dir, reason="test"
    )

    assert os.path.isfile(path)
    ok, detail = database_backup.verify_backup(path)
    assert ok, detail

    entries = database_backup.read_manifest(backup_dir)
    assert entries[-1]["result"] == "ok"
    assert entries[-1]["reason"] == "test"
    assert entries[-1]["filename"] == os.path.basename(path)


def test_backup_contains_the_same_data_as_the_database(db_path, backup_dir):
    _insert_product(db_path)
    path = database_backup.create_backup(db_path=db_path, backup_dir=backup_dir)

    connection = sqlite3.connect(path)
    try:
        rows = connection.execute("SELECT name FROM products").fetchall()
    finally:
        connection.close()

    assert rows == [("producto",)]


def test_backup_does_not_overwrite_previous_backups(db_path, backup_dir):
    first = database_backup.create_backup(db_path=db_path, backup_dir=backup_dir)
    second = database_backup.create_backup(db_path=db_path, backup_dir=backup_dir)

    assert first != second
    assert os.path.isfile(first)
    assert os.path.isfile(second)


def test_backup_of_missing_database_fails(tmp_path, backup_dir):
    missing = str(tmp_path / "no-existe.db")

    with pytest.raises(BackupError, match="No hay base de datos"):
        database_backup.create_backup(db_path=missing, backup_dir=backup_dir)


def test_retention_keeps_only_the_configured_amount(db_path, backup_dir, monkeypatch):
    monkeypatch.setenv(database_backup.ENV_RETENTION, "3")

    for _ in range(5):
        database_backup.create_backup(db_path=db_path, backup_dir=backup_dir)

    assert len(database_backup.list_backups(backup_dir)) == 3


def test_invalid_retention_falls_back_to_default(monkeypatch):
    monkeypatch.setenv(database_backup.ENV_RETENTION, "cero")
    assert database_backup.retention_limit() == database_backup.DEFAULT_RETENTION

    monkeypatch.setenv(database_backup.ENV_RETENTION, "0")
    assert database_backup.retention_limit() == database_backup.DEFAULT_RETENTION


def test_verify_rejects_missing_file(tmp_path):
    ok, detail = database_backup.verify_backup(str(tmp_path / "nada.db"))
    assert ok is False
    assert "no existe" in detail


def test_verify_rejects_non_database_file(tmp_path):
    path = tmp_path / "roto.db"
    path.write_bytes(b"no es una base sqlite")

    ok, _ = database_backup.verify_backup(str(path))
    assert ok is False


def test_verify_rejects_incomplete_database(tmp_path):
    path = tmp_path / "incompleta.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE products (id INTEGER)")
    connection.commit()
    connection.close()

    ok, detail = database_backup.verify_backup(str(path))
    assert ok is False
    assert "Faltan tablas" in detail


def test_scheduled_backup_skips_empty_database(db_path, backup_dir):
    assert (
        database_backup.maybe_scheduled_backup(
            db_path=db_path, backup_dir=backup_dir
        )
        is None
    )


def test_scheduled_backup_respects_interval(db_path, backup_dir, monkeypatch):
    _insert_product(db_path)
    monkeypatch.setenv(database_backup.ENV_INTERVAL, "24")

    first = database_backup.maybe_scheduled_backup(
        db_path=db_path, backup_dir=backup_dir
    )
    assert first is not None

    # Recien creada: no corresponde otra copia.
    assert (
        database_backup.maybe_scheduled_backup(
            db_path=db_path, backup_dir=backup_dir
        )
        is None
    )

    # Envejecemos la copia 25 horas: ahora si corresponde.
    old = time.time() - 25 * 3600
    os.utime(first, (old, old))

    second = database_backup.maybe_scheduled_backup(
        db_path=db_path, backup_dir=backup_dir
    )
    assert second is not None
    assert second != first
