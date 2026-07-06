from sqlalchemy.orm import Session
from sqlalchemy import desc
from Backend.models.sale import Sale
from Backend.models.item_sale import SaleItem
from Backend.models.product import Product
from datetime import datetime
from Backend.repositories.repository_base import RepositoryBase
from typing import List


class SaleRepository(RepositoryBase[Sale]):
    """Repository for sale database operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, Sale)
        self.db = db
    
    def get_pending_sale(self) -> Sale:
        """Gets the most recent pending sale"""
        return self.db.query(Sale).filter(Sale.state == "pending").order_by(desc(Sale.created_at)).first()
    
    def add_item_to_sale(self, item: SaleItem) -> SaleItem:
        """Adds or updates an item in a sale"""
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
    
    def get_item_by_sale_and_product(self, sale_id: int, product_id: int) -> SaleItem:
        """Gets a specific item from a sale by product"""
        return self.db.query(SaleItem).filter(
            SaleItem.sale_id == sale_id,
            SaleItem.product_id == product_id
        ).first()
    
    def update_total(self, sale: Sale) -> Sale:
        """Commits changes to a sale after updating total or state"""
        self.db.commit()
        self.db.refresh(sale)
        return sale
    
    def delete_item(self, sale_id: int, item_id: int) -> bool:
        """Deletes an item from a sale"""
        item = self.db.query(SaleItem).filter(
            SaleItem.sale_id == sale_id,
            SaleItem.id == item_id
        ).first()
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False

    def get_item_by_id(self, item_id: int) -> SaleItem:
        """Gets a sale item by its ID"""
        return self.db.query(SaleItem).filter(SaleItem.id == item_id).first()

    def get_items(self, sale_id: int) -> List[SaleItem]:
        """Gets all items for a given sale"""
        return self.db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
    
    def get_item_by_id_and_sale(self, sale_id: int, item_id: int) -> SaleItem:
        """Gets a specific item from a sale by its ID"""
        return self.db.query(SaleItem).filter(
            SaleItem.sale_id == sale_id,
            SaleItem.id == item_id
        ).first()
    
    def remove_item_from_sale(self, item: SaleItem) -> bool:
        """Removes an item from a sale"""
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False
    
    def get_recent_sales(self):
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(hours=24)
        sales = self.db.query(Sale).filter(Sale.created_at >= cutoff).order_by(desc(Sale.created_at)).all()
        for sale in sales:
            sale.items = self.db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
            for item in sale.items:
                item.product = self.db.query(Product).filter(Product.id == item.product_id).first()
        return sales

    def get_sales_by_date(self, date):
        from datetime import datetime, timedelta
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)
        sales = self.db.query(Sale).filter(Sale.created_at >= start, Sale.created_at < end).all()
        for sale in sales:
            sale.items = self.db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
            for item in sale.items:
                item.product = self.db.query(Product).filter(Product.id == item.product_id).first()
        return sales
    
    def update_item(self, item: SaleItem) -> SaleItem:
        """Updates an item in a sale"""
        self.db.commit()
        self.db.refresh(item)
        return item