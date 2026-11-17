"""Carpeta de datos del usuario y semilla inicial."""

import os

from Backend import runtime


def test_seed_path_never_points_to_the_development_database():
    seed = os.path.abspath(runtime.seed_db_path())
    expected_dir = os.path.abspath(
        os.path.join(os.path.dirname(os.path.dirname(runtime.__file__)), "installer", "seed")
    )

    assert os.path.dirname(seed) == expected_dir
    assert os.path.basename(seed) == "pos.db"


def test_ensure_seed_database_does_not_copy_the_development_database(
    monkeypatch, tmp_path
):
    # Simula un repo cuyo root tiene un pos.db (la base de desarrollo, con datos
    # reales) y una carpeta de datos descartable.
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pos.db").write_bytes(b"datos reales del comercio")
    data_dir = tmp_path / "datos"

    monkeypatch.setattr(runtime, "_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("ESCANAPP_DATA_DIR", str(data_dir))

    assert runtime.ensure_seed_database() is False
    assert not (data_dir / "pos.db").exists()


def test_ensure_seed_database_reports_false_when_there_is_no_seed(monkeypatch, tmp_path):
    monkeypatch.setenv("ESCANAPP_DATA_DIR", str(tmp_path / "datos"))

    assert runtime.ensure_seed_database() is False


def test_data_dir_honors_the_environment_override(monkeypatch, tmp_path):
    target = tmp_path / "otra-carpeta"
    monkeypatch.setenv("ESCANAPP_DATA_DIR", str(target))

    assert runtime.data_dir() == str(target)
    assert target.is_dir()
    assert runtime.backups_dir() == str(target / "backups")
