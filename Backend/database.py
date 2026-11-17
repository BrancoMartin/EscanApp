"""Acceso a la base SQLite y arranque del esquema.

El esquema NO se crea con ``Base.metadata.create_all()``: lo crean y lo
evolucionan las migraciones versionadas de Alembic (``Backend/migrations``).
``init_db()`` es el punto explicito donde se aplican, garantizado antes de que
cualquier sesion de negocio toque la base.

``Base`` se re-exporta desde aca por compatibilidad: los modelos y el ``env.py``
de Alembic lo importan directamente de ``Backend.models.base`` para no disparar
la preparacion de la carpeta de datos ni la creacion del engine.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend import runtime
from Backend.models.base import Base  # noqa: F401  (re-export historico)


# Prepara la carpeta de datos del usuario ANTES de tocar la base: si es su
# primer arranque, copia los Modelfiles y, si existiera una semilla, la base
# inicial. Es idempotente.
runtime.ensure_user_data()

# La base vive en la carpeta de datos del usuario, NO junto al ejecutable.
# Instalada en C:\Program Files, Windows no deja escribir ahi sin elevacion y
# SQLite abriria la base en modo lectura: la primera venta fallaria con
# "attempt to write a readonly database".
BASE_DIR = runtime.data_dir()
DATABASE_URL = f"sqlite:///{runtime.db_path()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Aplica las migraciones pendientes y los backups de arranque.

    Delega en el runner, que clasifica la base (nueva, ya versionada, 1.0.x sin
    registro de version, vacia o desconocida), respalda antes de migrar una base
    con datos y aplica Alembic hasta la ultima revision.

    Si algo falla, propaga la excepcion: la aplicacion NO debe arrancar con un
    esquema a medio migrar.
    """
    from Backend.migrations_runner import run_startup_migrations

    return run_startup_migrations()


def get_db():
    # Generador de sesión para usar como dependencia en FastAPI
    db = SessionLocal()
    try:
        yield db
    finally:
        # Cerramos la sesión siempre, haya error o no
        db.close()
