"""Productos: alta, consulta, actualizacion, codigo de barras e integridad."""

import pytest
from sqlalchemy.exc import IntegrityError

from Backend.models.product import Product
from Backend.services.product_service import ProductService


def test_create_product_persists_normalized_fields(session):
    service = ProductService(session)

    result = service.create("7790001", "Coca Cola", 1500.0, "Botella 2L", "Coca")

    assert result["success"] is True
    product_id = result["product"]["id"]

    saved = service.get_by_id(product_id)
    assert saved.name == "coca cola"
    assert saved.description == "botella 2l"
    assert saved.proveedor == "coca"
    assert saved.price == 1500.0
    assert saved.barcode == "7790001"


def test_create_product_allows_missing_optional_fields(session):
    service = ProductService(session)

    result = service.create("7790002", "Agua", 900.0)

    saved = service.get_by_id(result["product"]["id"])
    assert saved.description is None
    assert saved.proveedor is None


def test_get_all_and_get_by_barcode(session):
    service = ProductService(session)
    service.create("7790003", "Pan", 500.0)
    service.create("7790004", "Leche", 1200.0)

    assert len(service.get_all()) == 2
    assert service.get_by_barcode("7790004").name == "leche"

    with pytest.raises(ValueError, match="Product not found"):
        service.get_by_barcode("0000000")


@pytest.mark.parametrize(
    "barcode,name,price,message",
    [
        ("", "Producto", 10.0, "El codigo de barras es obligatorio"),
        ("123", "   ", 10.0, "El nombre del producto es obligatorio"),
        ("123", "Producto", 0, "El precio del producto debe ser mayor que cero"),
        ("123", "Producto", -5, "El precio del producto debe ser mayor que cero"),
    ],
)
def test_create_product_validates_required_fields(session, barcode, name, price, message):
    service = ProductService(session)

    with pytest.raises(ValueError, match=message):
        service.create(barcode, name, price)


def test_create_product_rejects_duplicate_barcode(session):
    service = ProductService(session)
    service.create("7790005", "Yerba", 2200.0)

    with pytest.raises(
        ValueError, match="Ya existe un producto con ese codigo de barras"
    ):
        service.create("7790005", "Otro producto", 100.0)


def test_create_product_rejects_duplicate_name_and_description(session):
    service = ProductService(session)
    service.create("7790006", "Azucar", 1300.0, "1 kg")

    with pytest.raises(
        ValueError, match="Ya existe un producto con ese nombre y descripcion"
    ):
        service.create("7790007", "azucar", 1400.0, "1 kg")


def test_update_product_changes_fields_and_saves(session):
    service = ProductService(session)
    created = service.create("7790008", "Fideos", 800.0, "500 g", "Proveedor")
    product_id = created["product"]["id"]

    updated = service.update(
        product_id,
        barcode="7790099",
        name="Fideos Secos",
        price=950.0,
        description="500 g",
        proveedor="Otro",
    )

    assert updated.barcode == "7790099"
    assert updated.name == "fideos secos"
    assert updated.price == 950.0
    assert updated.proveedor == "otro"

    session.expire_all()
    assert service.get_by_id(product_id).name == "fideos secos"


def test_update_rejects_barcode_used_by_another_product(session):
    service = ProductService(session)
    first = service.create("7790010", "Arroz", 1100.0)["product"]["id"]
    service.create("7790011", "Sal", 400.0)

    with pytest.raises(
        ValueError, match="Another product with that barcode already exists"
    ):
        service.update(first, barcode="7790011")


def test_database_enforces_unique_barcode(session):
    session.add(Product(name="uno", price=10.0, barcode="7790012"))
    session.commit()

    session.add(Product(name="dos", price=20.0, barcode="7790012"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_database_enforces_not_null_price(session):
    session.add(Product(name="sin precio", barcode="7790013"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_database_enforces_unique_product_attribute_pair(session):
    from Backend.models.attribute import Attribute
    from Backend.models.category import Category
    from Backend.models.product_attribute import ProductAttribute

    category = Category(name="categoria")
    session.add(category)
    session.commit()

    product = Product(name="producto", price=10.0, barcode="7790014")
    attribute = Attribute(name="atributo", category_id=category.id)
    session.add_all([product, attribute])
    session.commit()

    session.add(ProductAttribute(product_id=product.id, attribute_id=attribute.id))
    session.commit()

    session.add(ProductAttribute(product_id=product.id, attribute_id=attribute.id))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
