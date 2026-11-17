"""Fixtures de la suite.

Reglas no negociables:

- Ninguna prueba toca ``<repo>/pos.db`` ni ``%LOCALAPPDATA%\\EscanApp`` reales.
  ``ESCANAPP_DATA_DIR`` se apunta a un directorio temporal ANTES de importar
  cualquier modulo de ``Backend``, por si algun import resuelve la carpeta de
  datos.
- Cada prueba que necesita base recibe una base SQLite nueva dentro de
  ``tmp_path``, creada aplicando las migraciones reales.
- No se usa Ollama ni ningun servicio externo: solo servicios y repositorios.
"""

import os
import shutil
import tempfile

# Antes de los imports de Backend. Si algun modulo resuelve data_dir() al
# importarse, cae en un temporal y nunca en los datos reales del comercio.
SESSION_DATA_DIR = tempfile.mkdtemp(prefix="escanapp-tests-data-")
os.environ["ESCANAPP_DATA_DIR"] = SESSION_DATA_DIR

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from Backend import migrations_runner  # noqa: E402


def _silent(*args, **kwargs):
    """Log del runner silenciado: la suite no necesita stdout de migraciones."""


def pytest_sessionfinish(session, exitstatus):
    """La carpeta de datos de la sesion es descartable: no la dejamos en %TEMP%."""
    shutil.rmtree(SESSION_DATA_DIR, ignore_errors=True)


@pytest.fixture
def backup_dir(tmp_path):
    path = tmp_path / "backups"
    path.mkdir()
    return str(path)


@pytest.fixture
def db_path(tmp_path, backup_dir):
    """Base nueva, creada por las migraciones reales (instalacion nueva)."""
    path = str(tmp_path / "pos.db")
    migrations_runner.run_migrations(
        db_path=path, backup_dir=backup_dir, log=_silent
    )
    return path


@pytest.fixture
def engine(db_path):
    created = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    try:
        yield created
    finally:
        created.dispose()


@pytest.fixture
def session(engine):
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    created = factory()
    try:
        yield created
    finally:
        created.close()
