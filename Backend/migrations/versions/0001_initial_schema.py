"""Revision base: esquema de EscanApp 1.0.1.

Esta revision reproduce el DDL REAL que existia antes de Alembic, tal como lo
creaban ``Base.metadata.create_all()`` y ``installer/seed/pos.db``:

- 6 tablas: categories, products, attributes, product_attributes, sales, sale_items
- 7 indices: ix_attributes_id, ix_categories_name (unique), ix_products_barcode
  (unique), ix_products_id, ix_products_name, ix_sale_items_id, ix_sales_id
- ``CONSTRAINT uq_category_attribute UNIQUE (category_id, name)`` en attributes
- ``UNIQUE (product_id, attribute_id)`` SIN nombre en product_attributes
- ``sales.state`` como VARCHAR(9) sin CHECK (Enum con create_constraint=False)

IMPORTANTE: las tablas se crean con SQL explicito, no con ``op.create_table``.
Alembic hereda la ``naming_convention`` de ``target_metadata`` y nombraria las
PK, FK y la restriccion unica sin nombre, generando un DDL distinto al de las
bases 1.0.x ya existentes. Una base sellada en esta revision tiene que coincidir
exactamente con lo que esta revision describe; los nombres nuevos se aplican
solo a restricciones creadas por migraciones FUTURAS.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-17
"""

from alembic import op


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE categories (
            id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            created_at DATETIME,
            PRIMARY KEY (id)
        )
        """
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)

    op.execute(
        """
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
        )
        """
    )
    op.create_index("ix_products_barcode", "products", ["barcode"], unique=True)
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index("ix_products_name", "products", ["name"], unique=False)

    op.execute(
        """
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
        )
        """
    )
    op.create_index("ix_attributes_id", "attributes", ["id"], unique=False)

    op.execute(
        """
        CREATE TABLE product_attributes (
            id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            attribute_id INTEGER NOT NULL,
            created_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (product_id, attribute_id),
            FOREIGN KEY(product_id) REFERENCES products (id),
            FOREIGN KEY(attribute_id) REFERENCES attributes (id)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE sales (
            id INTEGER NOT NULL,
            total_price FLOAT NOT NULL,
            created_at DATETIME,
            state VARCHAR(9),
            PRIMARY KEY (id)
        )
        """
    )
    op.create_index("ix_sales_id", "sales", ["id"], unique=False)

    op.execute(
        """
        CREATE TABLE sale_items (
            id INTEGER NOT NULL,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price FLOAT NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(sale_id) REFERENCES sales (id),
            FOREIGN KEY(product_id) REFERENCES products (id)
        )
        """
    )
    op.create_index("ix_sale_items_id", "sale_items", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sale_items_id", table_name="sale_items")
    op.drop_table("sale_items")

    op.drop_index("ix_sales_id", table_name="sales")
    op.drop_table("sales")

    op.drop_table("product_attributes")

    op.drop_index("ix_attributes_id", table_name="attributes")
    op.drop_table("attributes")

    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_id", table_name="products")
    op.drop_index("ix_products_barcode", table_name="products")
    op.drop_table("products")

    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")
