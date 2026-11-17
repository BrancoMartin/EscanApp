"""Helpers compartidos por la suite: esquema 1.0.1 y firmas de esquema.

El DDL de ``LEGACY_SCHEMA`` es el que existia antes de Alembic (relevado de
``installer/seed/pos.db`` y del ``pos.db`` de desarrollo, ambos identicos).
Se conserva aca como referencia congelada: sirve para armar una instalacion
"vieja" con datos y para comparar que una instalacion nueva sea indistinguible
de una migrada.
"""

import sqlite3


LEGACY_SCHEMA = """
CREATE TABLE categories (
    id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    created_at DATETIME,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_categories_name ON categories (name);

CREATE TABLE products (
    id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    proveedor VARCHAR,
    price FLOAT NOT NULL,
    barcode VARCHAR NOT NULL,
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_products_barcode ON products (barcode);
CREATE INDEX ix_products_id ON products (id);
CREATE INDEX ix_products_name ON products (name);

CREATE TABLE attributes (
    id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    category_id INTEGER,
    amount_products INTEGER,
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT uq_category_attribute UNIQUE (category_id, name),
    FOREIGN KEY(category_id) REFERENCES categories (id)
);
CREATE INDEX ix_attributes_id ON attributes (id);

CREATE TABLE product_attributes (
    id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    attribute_id INTEGER NOT NULL,
    created_at DATETIME,
    PRIMARY KEY (id),
    UNIQUE (product_id, attribute_id),
    FOREIGN KEY(product_id) REFERENCES products (id),
    FOREIGN KEY(attribute_id) REFERENCES attributes (id)
);

CREATE TABLE sales (
    id INTEGER NOT NULL,
    total_price FLOAT NOT NULL,
    created_at DATETIME,
    state VARCHAR(9),
    PRIMARY KEY (id)
);
CREATE INDEX ix_sales_id ON sales (id);

CREATE TABLE sale_items (
    id INTEGER NOT NULL,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price FLOAT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(sale_id) REFERENCES sales (id),
    FOREIGN KEY(product_id) REFERENCES products (id)
);
CREATE INDEX ix_sale_items_id ON sale_items (id);
"""


LEGACY_DATA = """
INSERT INTO categories (id, name, created_at) VALUES
    (1, 'gaseosas', '2026-01-02 10:00:00'),
    (2, 'almacen', '2026-01-02 10:00:00');

INSERT INTO attributes (id, name, category_id, amount_products, created_at, updated_at) VALUES
    (1, 'sabor', 1, 1, '2026-01-02 10:00:00', '2026-01-02 10:00:00'),
    (2, 'marca', 2, 1, '2026-01-02 10:00:00', '2026-01-02 10:00:00');

INSERT INTO products (id, name, description, proveedor, price, barcode, created_at, updated_at) VALUES
    (1, 'coca cola', 'botella', 'coca', 1500.0, '7790001', '2026-01-02 10:00:00', '2026-01-02 10:00:00'),
    (2, 'agua', NULL, NULL, 900.0, '7790002', '2026-01-02 10:00:00', '2026-01-02 10:00:00'),
    (3, 'pan', NULL, NULL, 500.0, '7790003', '2026-01-02 10:00:00', '2026-01-02 10:00:00');

INSERT INTO product_attributes (id, product_id, attribute_id, created_at) VALUES
    (1, 1, 1, '2026-01-02 10:00:00'),
    (2, 1, 2, '2026-01-02 10:00:00');

INSERT INTO sales (id, total_price, created_at, state) VALUES
    (1, 3000.0, '2026-01-02 10:05:00', 'closed');

INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 2, 1500.0);
"""


def create_legacy_database(path, with_data=True):
    """Crea una base con el esquema exacto de 1.0.1 (sin tabla de version)."""
    connection = sqlite3.connect(path)
    try:
        connection.executescript(LEGACY_SCHEMA)
        if with_data:
            connection.executescript(LEGACY_DATA)
        connection.commit()
    finally:
        connection.close()
    return path


def count_rows(db_path, table):
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()
        return row[0] if row else 0
    finally:
        connection.close()


def _normalize_sql(sql):
    return " ".join((sql or "").split())


def schema_signature(db_path):
    """Firma estructural de una base, ignorando ``alembic_version``.

    Compara tablas, columnas (nombre, tipo, nullabilidad, default, PK), indices
    propios y claves foraneas. Dos bases con la misma firma son indistinguibles
    para la aplicacion.
    """
    connection = sqlite3.connect(db_path)
    try:
        signature = {}
        rows = connection.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' "
            "AND name != 'alembic_version' "
            "ORDER BY name"
        ).fetchall()

        for name, sql in rows:
            columns = connection.execute(f'PRAGMA table_info("{name}")').fetchall()
            index_rows = connection.execute(f'PRAGMA index_list("{name}")').fetchall()
            foreign_keys = connection.execute(
                f'PRAGMA foreign_key_list("{name}")'
            ).fetchall()

            indexes = []
            for index_row in index_rows:
                index_name = index_row[1]
                if index_name.startswith("sqlite_autoindex_"):
                    continue
                index_columns = connection.execute(
                    f'PRAGMA index_info("{index_name}")'
                ).fetchall()
                indexes.append(
                    (
                        index_name,
                        index_row[2],
                        tuple(column[2] for column in index_columns),
                    )
                )

            signature[name] = {
                "sql": _normalize_sql(sql),
                "columns": [
                    (column[1], column[2], column[3], column[4], column[5])
                    for column in columns
                ],
                "indexes": sorted(indexes),
                "foreign_keys": sorted(
                    (fk[2], fk[3], fk[4]) for fk in foreign_keys
                ),
            }
        return signature
    finally:
        connection.close()
