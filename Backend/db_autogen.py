"""Filtros compartidos por el ``env.py`` de Alembic y las pruebas de deriva.

Existe una unica diferencia conocida y DELIBERADA entre los modelos y el DDL
real de 1.0.1: ``product_attributes`` tiene
``UNIQUE (product_id, attribute_id)`` SIN nombre (SQLite la materializa como
``sqlite_autoindex_product_attributes_1``), mientras que la ``naming_convention``
de la metadata le asigna ``uq_product_attributes_product_id``.

Renombrar esa restriccion en una base de cliente es una migracion explicita
posterior (deuda anotada en el change ``database-migrations``), no un efecto
secundario de la adopcion de Alembic. Mientras esa migracion no exista, el
filtro evita que ``--autogenerate`` proponga "arreglar" el nombre en cada
generacion de revision. Cualquier otra diferencia SI se reporta.
"""

_UQ_PRODUCT_ATTRIBUTES = "uq_product_attributes_product_id"


def include_object(obj, name, type_, reflected, compare_to):
    """Devuelve False solo para la restriccion unica sin nombre de 1.0.1."""
    if type_ != "unique_constraint":
        return True
    if name != _UQ_PRODUCT_ATTRIBUTES:
        return True

    table = getattr(obj, "table", None)
    if table is None or getattr(table, "name", None) != "product_attributes":
        return True

    columns = [column.name for column in getattr(obj, "columns", [])]
    if columns != ["product_id", "attribute_id"]:
        return True

    # Es exactamente la restriccion conocida: se ignora en la comparacion.
    return False
