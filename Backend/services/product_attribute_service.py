from sqlalchemy.orm import Session
from Backend.repositories.product_attribute_repository import ProductAttributeRepository
from Backend.repositories.product_repository import ProductRepository
from Backend.models.product_attribute import ProductAttribute
from Backend.models.attribute import Attribute
from typing import List



class ProductAttributeService: 

    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductAttributeRepository(db)
        self.product = ProductRepository(db)

    def get_all(self) -> List[ProductAttribute]:
        return self.repo.get_all()
    
    def _increment_attribute_count(self, attribute_id: int):
        attribute = self.db.query(Attribute).filter(Attribute.id == attribute_id).first()
        if attribute:
            attribute.amount_products = (attribute.amount_products or 0) + 1
            self.db.commit()
    
    def _decrement_attribute_count(self, attribute_id: int):
        attribute = self.db.query(Attribute).filter(Attribute.id == attribute_id).first()
        if attribute and attribute.amount_products and attribute.amount_products > 0:
            attribute.amount_products = attribute.amount_products - 1
            self.db.commit()
    
    def create(self, product_id, attribute_id) -> ProductAttribute:
        if not product_id:
            raise ValueError("El product id es obligatorio")
       
        if not attribute_id: 
            raise ValueError("el id del atributo no esta")

        product_attribute = ProductAttribute(product_id=product_id, attribute_id=attribute_id)
        response = self.repo.create(product_attribute)
        self._increment_attribute_count(attribute_id)

        return {
    "success": True,
    "attribute": {
        "product_id":product_id, 
        "attribute_id":attribute_id
    }}


    def get_by_name(self, name): 
        product = self.repo.get_by_name(name)
        return product

    
    def get_or_create(self, product_id, attribute_id):
        existing = self.repo.get_by_ids(product_id, attribute_id)
        if existing:
            return existing

        product_attribute = ProductAttribute(product_id=product_id, attribute_id=attribute_id)
        result = self.repo.create(product_attribute)
        self._increment_attribute_count(attribute_id)
        return result

    def assign_attribute_to_product(self, db: Session, product_id: int, attribute_id: int):
        result = self.assign_attribute_to_product(product_id, attribute_id)

        return result