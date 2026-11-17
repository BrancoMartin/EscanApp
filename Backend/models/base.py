"""Base declarativa de SQLAlchemy, sin efectos secundarios.

Vive en este modulo y no en ``Backend/database.py`` a proposito: el ``env.py``
de Alembic tiene que leer ``Base.metadata`` para detectar deriva, y si lo
importara desde ``Backend.database`` dispararia la preparacion de la carpeta de
datos y la creacion del engine como efecto colateral de generar una revision.
Importar este modulo solo define la metadata.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Convencion de nombres para las restricciones que se creen DE AHORA EN ADELANTE.
# SQLite no permite ALTER TABLE DROP/ALTER COLUMN: Alembic resuelve eso con el
# modo batch, que recrea la tabla y necesita poder nombrar cada restriccion.
# Las restricciones que ya existen en bases 1.0.x se mantienen como estan: la
# revision base reproduce el DDL real y no renombra nada.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
