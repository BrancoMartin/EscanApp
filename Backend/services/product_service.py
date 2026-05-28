from sqlalchemy.orm import Session
from repositories.product_repository import ProductRepository
from models.product import Product
from typing import List


class ProductService:
    """Business logic service for products"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)
  
    
    def get_all(self) -> List[Product]:
        return self.repo.get_all()
    
    def get_by_barcode(self, barcode: str) -> Product:
        product = self.repo.get_by_barcode(barcode)
        if not product:
            raise ValueError("Product not found")
        return product
    
    def get_by_id(self, product_id: int) -> Product:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        return product
    


    def create(self, barcode: str, name: str, price: float, description: str = None) -> Product:
        if not barcode or barcode.strip() == "":
            raise ValueError("El codigo de barras es obligatorio")
        if not name or name.strip() == "":
            raise ValueError("El nombre del producto es obligatorio")
        if price is None or price <= 0:
            raise ValueError("El precio del producto debe ser mayor que cero")
        if self.repo.get_by_barcode(barcode):
            raise ValueError("Ya existe un producto con ese codigo de barras")
       

        product = Product(name=name, description=description, price=price, barcode=barcode)
        response = self.repo.create(product)

        return {
    "success": True,
    "product": {
        "id": response.id,
        "name": response.name,
        "price": response.price,
        "barcode": response.barcode,
        "description": response.description
    }}
    






    def update(self, product_id: int, barcode: str = None, name: str = None, 
               price: float = None, description: str = None) -> Product:
        product = self.get_by_id(product_id)
        if barcode is not None:
            existing = self.repo.get_by_barcode(barcode)
            if existing and existing.id != product_id:
                raise ValueError("Another product with that barcode already exists")
            product.barcode = barcode
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price
        return self.repo.update(product)
    
    def delete(self, product_id: int) -> bool:
        return self.repo.delete(product_id)
    

    def get_products_by_attribute(self, attribute_id): 
        try: 
            products = self.get_products_by_attributes(attribute_id)
        except Exception as e: 
            print(f"Error extracting attributes: {e}")

        return products
    
    def get_product_by_value(self, id_value):
        products = self.repo.get_product_by_value(id_value)

        if not products: 
            raise FileNotFoundError("no se encontraron productos")
        
        return products