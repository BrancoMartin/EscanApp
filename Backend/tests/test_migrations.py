"""Base de datos: instalacion nueva, adopcion de 1.0.x, casos inseguros y deriva."""

import hashlib
import sqlite3

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from Backend import database_state, migrations_runner
from Backend.db_autogen import include_object
from Backend.tests import support


def _silent(*args, **kwargs):
    pass


def _sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def test_fresh_install_creates_schema_at_head(tmp_path, backup_dir):
    db = str(tmp_path / "pos.db")

    report = migrations_runner.run_migrations(
        db_path=db, backup_dir=backup_dir, log=_silent
    )

    assert report["case"] == "A"
    assert report["applied"] is True
    assert report["backup"] is None
    assert database_state.schema_revision(db) == report["head"]
    assert set(database_state.EXPECTED_TABLES).issubset(
        database_state.existing_tables(db)
    )


def test_fresh_install_is_indistinguishable_from_legacy_schema(tmp_path, backup_dir):
    fresh = str(tmp_path / "fresh.db")
    legacy = str(tmp_path / "legacy.db")
    support.create_legacy_database(legacy, with_data=False)

    migrations_runner.run_migrations(db_path=fresh, backup_dir=backup_dir, log=_silent)

    assert support.schema_signature(fresh) == support.schema_signature(legacy)


def test_base_revision_keeps_legacy_constraint_names(tmp_path, backup_dir):
    db = str(tmp_path / "pos.db")
    migrations_runner.run_migrations(db_path=db, backup_dir=backup_dir, log=_silent)

    connection = sqlite3.connect(db)
    try:
        sql = dict(
            connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        )
    finally:
        connection.close()

    assert "CONSTRAINT uq_category_attribute UNIQUE" in sql["attributes"]
    assert "CONSTRAINT uq_" not in sql["product_attributes"]
    # Ni la naming_convention nueva ni nombres inventados se filtran al DDL real.
    for statement in sql.values():
        assert "CONSTRAINT pk_" not in statement
        assert "CONSTRAINT fk_" not in statement


def test_legacy_database_is_adopted_without_losing_data(tmp_path, backup_dir):
    db = str(tmp_path / "pos.db")
    support.create_legacy_database(db, with_data=True)
    before = database_state.table_row_counts(db)

    report = migrations_runner.run_migrations(
        db_path=db, backup_dir=backup_dir, log=_silent
    )

    assert report["case"] == "C"
    assert report["applied"] is True
    assert database_state.schema_revision(db) == report["head"]
    assert database_state.table_row_counts(db) == before
    assert before["products"] == 3
    assert before["sale_items"] == 1

    assert report["backup"] is not None
    assert database_verify(report["backup"]) is True


def database_verify(path):
    from Backend.database_backup import verify_backup

    ok, _ = verify_backup(path)
    return ok


def test_adoption_preserves_business_data(tmp_path, backup_dir):
    db = str(tmp_path / "pos.db")
    support.create_legacy_database(db, with_data=True)

    migrations_runner.run_migrations(db_path=db, backup_dir=backup_dir, log=_silent)

    connection = sqlite3.connect(db)
    try:
        name, price, barcode = connection.execute(
            "SELECT name, price, barcode FROM products WHERE id = 1"
        ).fetchone()
        total, state = connection.execute(
            "SELECT total_price, state FROM sales WHERE id = 1"
        ).fetchone()
    finally:
        connection.close()

    assert (name, price, barcode) == ("coca cola", 1500.0, "7790001")
    assert (total, state) == (3000.0, "closed")


def test_legacy_database_without_data_is_not_backed_up(tmp_path, backup_dir):
    db = str(tmp_path / "pos.db")
    support.create_legacy_database(db, with_data=False)

    report = migrations_runner.run_migrations(
        db_path=db, backup_dir=backup_dir, log=_silent
    )

    assert report["case"] == "C"
    assert report["backup"] is None


def test_second_startup_is_a_noop_and_creates_no_backup(tmp_path, backup_dir):
    db = str(tmp_path / "pos.db")
    support.create_legacy_database(db, with_data=True)

    first = migrations_runner.run_migrations(
        db_path=db, backup_dir=backup_dir, log=_silent
    )
    second = migrations_runner.run_migrations(
        db_path=db, backup_dir=backup_dir, log=_silent
    )

    assert first["applied"] is True
    assert second["applied"] is False
    assert second["case"] == "B"
    assert second["backup"] is None

    from Backend import database_backup

    assert len(database_backup.list_backups(backup_dir)) == 1


def test_unknown_database_is_never_modified(tmp_path, backup_dir):
    db = str(tmp_path / "foreign.db")
    connection = sqlite3.connect(db)
    connection.execute("CREATE TABLE foo (id INTEGER)")
    connection.commit()
    connection.close()
    before = _sha256(db)

    with pytest.raises(migrations_runner.MigrationError, match="no se reconoce"):
        migrations_runner.run_migrations(db_path=db, backup_dir=backup_dir, log=_silent)

    assert _sha256(db) == before
    assert database_state.schema_revision(db) is None


def test_corrupt_file_is_never_modified(tmp_path, backup_dir):
    db = str(tmp_path / "corrupt.db")
    with open(db, "wb") as handle:
        handle.write(b"this is not a sqlite database")
    before = _sha256(db)

    with pytest.raises(migrations_runner.MigrationError):
        migrations_runner.run_migrations(db_path=db, backup_dir=backup_dir, log=_silent)

    assert _sha256(db) == before


def test_empty_file_is_upgraded(tmp_path, backup_dir):
    db = str(tmp_path / "empty.db")
    connection = sqlite3.connect(db)
    connection.close()

    report = migrations_runner.run_migrations(
        db_path=db, backup_dir=backup_dir, log=_silent
    )

    assert report["case"] == "D"
    assert report["applied"] is True
    assert database_state.schema_revision(db) == report["head"]


def test_models_and_migrations_do_not_drift(tmp_path, backup_dir):
    db = str(tmp_path / "pos.db")
    migrations_runner.run_migrations(db_path=db, backup_dir=backup_dir, log=_silent)

    # Importar los 6 modelos registra la metadata completa.
    from Backend.models.base import Base
    from Backend.models import (  # noqa: F401
        attribute,
        category,
        item_sale,
        product,
        product_attribute,
        sale,
    )

    engine = create_engine(f"sqlite:///{db}")
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection,
                opts={"compare_type": True, "include_object": include_object},
            )
            differences = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()

    assert differences == []
