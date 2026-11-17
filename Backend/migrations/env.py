"""Entorno de Alembic para EscanApp.

Se usa de dos formas:

1. ``Backend/migrations_runner.py`` lo carga programaticamente en el arranque de
   la aplicacion, con ``script_location`` y ``sqlalchemy.url`` en memoria. En el
   ejecutable empaquetado NO se lee ``alembic.ini``.
2. El CLI de desarrollo (``python -m alembic -c Backend/alembic.ini ...``) lo usa
   para generar revisiones e inspeccionar el historial.

Importa ``Base`` y los modelos desde ``Backend.models.base``, que no tiene
efectos secundarios: generar una revision no debe crear la carpeta de datos ni
un engine.
"""

import os
import sys

from alembic import context
from sqlalchemy import create_engine, pool

# Deja el repositorio en sys.path: vale tanto para el CLI como para el runner,
# y tanto desde la raiz como desde Backend/.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from Backend import runtime  # noqa: E402
from Backend.db_autogen import include_object  # noqa: E402
from Backend.models.base import Base  # noqa: E402

# Importar los 6 modelos UNA sola vez registra sus tablas en Base.metadata.
# Sin estos imports, el autogenerate creeria que hay que borrar todas las tablas.
from Backend.models.category import Category  # noqa: E402,F401
from Backend.models.attribute import Attribute  # noqa: E402,F401
from Backend.models.product import Product  # noqa: E402,F401
from Backend.models.product_attribute import ProductAttribute  # noqa: E402,F401
from Backend.models.sale import Sale  # noqa: E402,F401
from Backend.models.item_sale import SaleItem  # noqa: E402,F401

config = context.config
target_metadata = Base.metadata


def _database_url():
    """URL configurada (CLI) o la de la base del usuario (runtime)."""
    configured = config.get_main_option("sqlalchemy.url")
    if configured:
        return configured
    return f"sqlite:///{runtime.db_path()}"


def _configure_logging():
    """El ini de desarrollo trae loggers; el Config del runner no tiene archivo."""
    if config.config_file_name is None:
        return
    try:
        from logging.config import fileConfig

        fileConfig(config.config_file_name, disable_existing_loggers=False)
    except Exception:
        # Un ini sin seccion de logging no debe romper una migracion.
        pass


def run_migrations_offline():
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        compare_type=True,
        include_object=include_object,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(_database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite no soporta DROP/ALTER COLUMN: el modo batch recrea la tabla
            # y copia los datos. compare_type detecta cambios de tipo.
            render_as_batch=True,
            compare_type=True,
            include_object=include_object,
            # Cada revision en su propia transaccion: si la tercera falla, las
            # anteriores quedan aplicadas y registradas, nunca a medio aplicar.
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


_configure_logging()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
