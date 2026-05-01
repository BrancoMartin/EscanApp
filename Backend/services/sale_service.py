from sqlalchemy.orm import Session
from repositories.sale_repository import SaleRepository
from models.sale import Sale
from models.item_sale import SaleItem
from models.product import Product
from datetime import datetime


class SaleService:

    def __init__(self, db: Session):
        self.repo = SaleRepository(db)
        

    def get_all(self):
        return [self._format_sale(s) for s in self.repo.get_all()]

    def get_pending(self):
        sale = self.repo.get_pending_sale()
        if not sale:
            return None
        return self._format_sale(sale)

    def create(self, items: list):
        sale = Sale(state="pending", total_price=0.0, created_at=datetime.now())
        sale = self.repo.create(sale)
        total = 0.0
        for item_data in items:
            pid = item_data.product_id if hasattr(item_data, 'product_id') else item_data['product_id']
            qty = item_data.quantity if hasattr(item_data, 'quantity') else item_data['quantity']
            up = item_data.unit_price if hasattr(item_data, 'unit_price') else item_data['unit_price']
            item = SaleItem(
                sale_id=sale.id,
                product_id=pid,
                quantity=qty,
                unit_price=up,
            )
            self.repo.add_item_to_sale(item)
            total += qty * up
        sale.total_price = total
        self.repo.db.commit()      # commit primero
        self.repo.db.refresh(sale) # refresh después
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
        sale.total_price = sum(i.quantity * i.unit_price for i in items)
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
        
        # Get or create pending sale
        pending_sale = self.repo.get_pending_sale()
        if not pending_sale:
            pending_sale = Sale(state="pending", total_price=0.0, created_at=datetime.now())
            pending_sale = self.repo.create(pending_sale)
        
        # Check if product already in sale
        existing_item = self.repo.get_item_by_sale_and_product(pending_sale.id, product.id)
        if existing_item:
            existing_item.quantity += 1
            self.repo.db.commit()
        else:
            item = SaleItem(
                sale_id=pending_sale.id,
                product_id=product.id,
                quantity=1,
                unit_price=product.price,
            )
            self.repo.add_item_to_sale(item)
        
        # Update total
        items = self.repo.get_items(pending_sale.id)
        pending_sale.total_price = sum(i.quantity * i.unit_price for i in items)
        self.repo.update_total(pending_sale)
        
        return {"success": True, "sale": self._format_sale(pending_sale)}


    def get_items(self, sale_id: int):
        return self.repo.get_items(sale_id)

    def _format_sale(self, sale: Sale):
        items = []
        for i in self.repo.get_items(sale.id):
            product = self.repo.db.query(Product).filter(Product.id == i.product_id).first()
            items.append({
                "id": i.id,
                "product_id": i.product_id,
                "product_name": product.name if product else "Unknown",
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "subtotal": i.quantity * i.unit_price,
            })
        return {
            "id": sale.id,
            "state": sale.state,
            "total_price": sale.total_price,
            "created_at": str(sale.created_at),
            "items": items,
        }