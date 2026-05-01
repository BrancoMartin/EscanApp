from sqlalchemy.orm import Session
from repositories.sale_repository import SaleRepository
from models.sale import Sale
from models.sale_item import SaleItem
from datetime import datetime


class SaleService:

    def __init__(self, db: Session):
        self.repo = SaleRepository(db)
        

    def get_history(self):
        sales = self.repo.get_all()
        return [self._format_sale(s) for s in sales]

    def create(self, items: list):
        sale = Sale(state="pending", total=0.0, created_at=datetime.now())
        sale = self.repo.create(sale)
        total = 0.0
        for item_data in items:
            item = SaleItem(
                sale_id=sale.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
            )
            self.repo.add_item_to_sale(item)
            total += item_data.quantity * item_data.unit_price
        sale.total = total
        self.repo.update_total(sale)
        return self._format_sale(sale)

    def close_sale(self, sale_id: int):
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            return {"error": "Sale not found"}
        sale.state = "closed"
        self.repo.update_total(sale)
        return self._format_sale(sale)

    def get_details(self, sale_id: int):
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            return None
        return self._format_sale(sale)

    def remove_item_from_sale(self, sale_id: int, item_id: int):
        deleted = self.repo.delete_item(sale_id, item_id)
        if not deleted:
            return {"error": "Item not found"}
        sale = self.repo.get_by_id(sale_id)
        items = self.repo.get_items(sale_id)
        sale.total = sum(i.quantity * i.unit_price for i in items)
        self.repo.update_total(sale)
        return self._format_sale(sale)

    def scan_product_by_barcode(self, barcode: str):
        from repositories.product_repository import ProductRepository
        from models.product import Product
        # Delegar al repo de productos
        repo = ProductRepository(self.repo.db)
        product = repo.get_by_barcode(barcode)
        if not product:
            return {"error": "Product not found"}
        return {"success": True, "product": product}

    def _format_sale(self, sale: Sale):
        items = self.repo.get_items(sale.id)
        return {
            "id": sale.id,
            "state": sale.state,
            "total": sale.total,
            "created_at": str(sale.created_at),
            "items": [
                {
                    "id": i.id,
                    "product_id": i.product_id,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                }
                for i in items
            ],
        }