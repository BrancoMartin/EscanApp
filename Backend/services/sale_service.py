from sqlalchemy.orm import Session
from repositories.sale_repository import SaleRepository
from models.sale import Sale
from models.item_sale import SaleItem
from models.product import Product
from datetime import datetime, date


class SaleService:

    def __init__(self, db: Session):
        self.repo = SaleRepository(db)

    def get_all(self):
        return [self._format_sale(s) for s in self.repo.get_all()]

    def get_pending(self):
        sale = self.repo.get_pending_sale()
        if not sale:
            return None
        return sale

    def create(self, items: list):
        sale = Sale(state="pending", total_price=0.0, created_at=date.today())
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
        self.repo.db.commit()
        self.repo.db.refresh(sale)
        return sale

    def close_sale(self, sale_id: int):
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            return {"error": "Sale not found"}
        sale.state = "closed"
        self.repo.update_total(sale)
        return sale

    def get_details(self, sale_id: int):
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            return None
        return sale

    def remove_item_from_sale(self, sale_id: int, item_id: int):
        print(f"SERVICE: Intentando eliminar item con ID {item_id} de la venta con ID {sale_id}")
        item = self.repo.get_item_by_id_and_sale(sale_id, item_id)
        if not item:
            return {"error": "Item not found"}
        print("ITEM ENCONTRADO:", item)
        sale = self.repo.get_by_id(sale_id)
        print("SALE ENCONTRADA:", sale)
        sale.total_price = sale.total_price - item.unit_price
        if sale.total_price < 0:
            sale.total_price = 0.0
        item.quantity = item.quantity - 1
        if item.quantity <= 0:
            response = self.repo.remove_item_from_sale(item)
            if not response:
                return {"error": "Failed to remove item from sale"}
        print("SALE ANTES DE ACTUALIZAR:", sale)
        self.repo.update_total(sale)
        return sale

    def scan_product_by_barcode(self, barcode: str):
        from repositories.product_repository import ProductRepository
        repo = ProductRepository(self.repo.db)
        product = repo.get_by_barcode(barcode)
        if not product:
            return {"error": "Product not found"}
        pending_sale = self.repo.get_pending_sale()
        if not pending_sale:
            pending_sale = Sale(state="pending", total_price=0.0, created_at=date.today())
            pending_sale = self.repo.create(pending_sale)
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
        items = self.repo.get_items(pending_sale.id)
        pending_sale.total_price = sum(i.quantity * i.unit_price for i in items)
        sale = self.repo.update_total(pending_sale)

        format_items = []
        for i in items:
            format_items.append({
                "id": i.id,
                "product_id": i.product_id,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "subtotal": i.quantity * i.unit_price
            })

        format_sale = {
            "sale": {
                "id": sale.id,
                "state": sale.state,
                "total_price": sale.total_price,
                "created_at": sale.created_at.strftime("%d/%m/%Y"),
            },
            "items": format_items
        }
        return format_sale

    def get_items(self, sale_id: int):
        return self.repo.get_items(sale_id)


    def get_item_by_id_and_sale(self, sale_id: int, item_id: int):
        return self.repo.get_item_by_id_and_sale(sale_id, item_id)

    def delete_sale(self, sale_id: int):
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            return {"error": "Sale not found"}
        self.repo.delete(sale)
        return {"success": True}

    def get_sales_by_date(self, date_str: str):

        print(f"BUSCANDO VENTAS PARA LA FECHA: {date_str}")

        parse_date = datetime .strptime(date_str.split(" ")[0], "%Y-%m-%d").date()
        
        print(f"FECHA PARSEADA: {parse_date}")

        sales = self.repo.get_sales_by_date(parse_date)
        
        print(f"SALES ENCONTRADAS PARA LA FECHA {parse_date}: {sales}")
        return sales