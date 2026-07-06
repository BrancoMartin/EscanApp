from sqlalchemy.orm import Session
from Backend.repositories.sale_repository import SaleRepository
from Backend.repositories.product_repository import ProductRepository
from Backend.models.sale import Sale
from Backend.models.item_sale import SaleItem
from datetime import datetime, date


class SaleService:

    def __init__(self, db: Session):
        self.repo = SaleRepository(db)
        self.product = ProductRepository(db)

    def get_all(self):
        sales = self.repo.get_all()
        return [self._format_sale(s) for s in sales]

    def get_pending(self):
        pending_sale = self.repo.get_pending_sale()
        if not pending_sale:
            return None
        return self._format_sale(pending_sale)

    def create(self, items: list):
        sale = Sale(state="pending", total_price=0.0, created_at=datetime.now())
        sale = self.repo.create(sale)
        total = 0.0
        for item_data in items:
            self.repo.add_item_to_sale(item_data)
            total += item_data['quantity'] * item_data['unit_price']
        sale.total_price = total
        self.repo.db.commit()
        self.repo.db.refresh(sale)
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
        print(f"INTENTANDO ELIMINAR EL ITEM {item_id} DE LA VENTA CON ID {sale_id}")
        item = self.repo.get_item_by_id_and_sale(sale_id, item_id)
        print(f"ITEM OBTENIDO: {item}")
        if not item:
            return {"error": "Item not found"}
        sale = self.repo.get_by_id(sale_id)
        print(f"VENTA OBTENIDA: {sale}")
        sale.total_price = sale.total_price - item.unit_price

        print(f"TOTAL ACTUALIZADO DE LA VENTA: {sale.total_price}")
        if item.quantity == 1:
            self.repo.remove_item_from_sale(item)
        else:
            item.quantity -= 1
            response = self.repo.update_item(item)
            
            print(f"RESPUESTA DE ACTUALIZAR ITEM: {response}")
            if not response:
                return {"error": "Error al querer eliminar una venta"}
        
        self.repo.update_total(sale)
        print(f"TOTAL ACTUALIZADO DE LA VENTA DESPUÉS DE ELIMINAR ITEM: {sale.total_price}")
        return self._format_sale(sale)

    def scan_product_by_barcode(self, barcode: str):
        product = self.product.get_by_barcode(barcode)
        if not product:
            return {"error": "Product not found"}
        pending_sale = self.repo.get_pending_sale()
        if not pending_sale:
            pending_sale = Sale(state="pending", total_price=0.0, created_at=datetime.now())
            pending_sale = self.repo.create(pending_sale)
        existing_item = self.repo.get_item_by_sale_and_product(pending_sale.id, product.id)
        if existing_item:
            new_quantity = existing_item.quantity + 1
            existing_item.quantity = new_quantity
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
        self.repo.update_total(pending_sale)
        return self._format_sale(pending_sale)

    def get_items(self, sale_id: int):
        return self.repo.get_items(sale_id)

    def _format_sale(self, sale: Sale):
        items = []
        for i in self.repo.get_items(sale.id):
            product = self.product.get_by_id(i.product_id)
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
            "created_at": sale.created_at.strftime("%d/%m/%Y %H:%M"),
            "items": items,
        }

    def get_item_by_id_and_sale(self, sale_id: int, item_id: int):
        return self.repo.get_item_by_id_and_sale(sale_id, item_id)

    def delete_sale(self, sale_id: int):
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            return {"error": "Sale not found"}
        self.repo.delete(sale)
        return {"success": True}

    def get_recent_sales(self):
        sales = self.repo.get_recent_sales()
        return [self._format_sale(s) for s in sales]

    def get_sales_by_date(self, date_str: str):
        try:
            print(f"BUSCANDO VENTAS PARA LA FECHA: {date_str}")
            parse_date = datetime.strptime(date_str.split(" ")[0], "%Y-%m-%d").date()
            print(f"FECHA PARSEADA: {parse_date}")
            sales = self.repo.get_sales_by_date(parse_date)
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD."}
        return [self._format_sale(s) for s in sales]
