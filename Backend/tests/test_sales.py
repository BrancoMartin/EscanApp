"""Ventas: registro por escaneo, calculos, persistencia y relaciones."""

from sqlalchemy.orm import sessionmaker

from Backend.models.item_sale import SaleItem
from Backend.models.sale import Sale
from Backend.services.product_service import ProductService
from Backend.services.sale_service import SaleService


def _create_product(session, barcode="7790100", name="Coca", price=1500.0):
    result = ProductService(session).create(barcode, name, price)
    return result["product"]["id"]


def test_scan_creates_pending_sale_with_correct_total(session):
    _create_product(session)
    service = SaleService(session)

    result = service.scan_product_by_barcode("7790100")

    assert result["state"] == "pending"
    assert result["total_price"] == 1500.0
    assert len(result["items"]) == 1
    assert result["items"][0]["quantity"] == 1
    assert result["items"][0]["subtotal"] == 1500.0
    assert result["items"][0]["product_name"] == "coca"


def test_scan_same_product_increments_quantity_and_recalculates_total(session):
    _create_product(session)
    service = SaleService(session)

    service.scan_product_by_barcode("7790100")
    result = service.scan_product_by_barcode("7790100")

    assert len(result["items"]) == 1
    assert result["items"][0]["quantity"] == 2
    assert result["total_price"] == 3000.0

    pending = service.get_pending()
    assert pending["id"] == result["id"]


def test_scan_unknown_barcode_returns_error(session):
    service = SaleService(session)

    result = service.scan_product_by_barcode("0000000")

    assert result == {"error": "Product not found"}
    assert service.get_pending() is None


def test_sale_items_keep_unit_price_snapshot(session):
    product_id = _create_product(session, price=1500.0)
    service = SaleService(session)

    sale = service.scan_product_by_barcode("7790100")

    # El precio del producto cambia despues de la venta: el total de la venta
    # no puede cambiar (el item guarda el precio del momento).
    ProductService(session).update(product_id, price=2000.0)
    session.expire_all()

    details = service.get_details(sale["id"])
    assert details["items"][0]["unit_price"] == 1500.0
    assert details["total_price"] == 1500.0


def test_close_sale_marks_closed_and_persists(session, engine):
    _create_product(session)
    service = SaleService(session)
    sale = service.scan_product_by_barcode("7790100")

    closed = service.close_sale(sale["id"])
    assert closed["state"] == "closed"

    other = sessionmaker(bind=engine)()
    try:
        stored = other.query(Sale).filter(Sale.id == sale["id"]).one()
        assert stored.state == "closed"
        assert stored.total_price == 1500.0
    finally:
        other.close()


def test_sale_relations_link_items_and_products(session):
    product_id = _create_product(session)
    service = SaleService(session)
    sale = service.scan_product_by_barcode("7790100")

    stored = session.query(Sale).filter(Sale.id == sale["id"]).one()
    assert len(stored.items) == 1

    item = session.query(SaleItem).filter(SaleItem.sale_id == sale["id"]).one()
    assert item.product is not None
    assert item.product.id == product_id
    assert item.product.name == "coca"


def test_remove_item_recalculates_total(session):
    _create_product(session)
    service = SaleService(session)
    sale = service.scan_product_by_barcode("7790100")
    sale = service.scan_product_by_barcode("7790100")
    item_id = sale["items"][0]["id"]

    reduced = service.remove_item_from_sale(sale["id"], item_id)
    assert reduced["items"][0]["quantity"] == 1
    assert reduced["total_price"] == 1500.0

    removed = service.remove_item_from_sale(sale["id"], item_id)
    assert removed["items"] == []
    assert removed["total_price"] == 0.0
