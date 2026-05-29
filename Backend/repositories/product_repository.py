from sqlalchemy.orm import Session
from models.product import Product

from repositories.repository_base import RepositoryBase


class ProductRepository(RepositoryBase[Product]):
    """Repository for product database operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, Product)
        self.db = db

    
    def get_by_barcode(self, barcode: str) -> Product:
        """Gets a product by barcode"""
        return self.db.query(Product).filter(Product.barcode == barcode).first()
    

    def get_by_name(self, name): 
        return self.db.query(Product).filter(Product.name == name).first()