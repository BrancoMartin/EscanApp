from sqlalchemy.orm import Session
from Backend.repositories.product_attribute_repository import ProductAttributeRepository
from Backend.repositories.product_repository import ProductRepository
from Backend.models.product_attribute import ProductAttribute
from typing import List



class ProductAttributeService: 

    def __init__(self, db: Session):
        self.repo = ProductAttributeRepository(db)
        self.product = ProductRepository(db)

    def get_all(self) -> List[ProductAttribute]:
        return self.repo.get_all()
    
    
    def create(self, product_id, attribute_id) -> ProductAttribute:
        if not product_id:
            raise ValueError("El product id es obligatorio")
       
        if not attribute_id: 
            raise ValueError("el id del atributo no esta")
       
        product_attribute = ProductAttribute(product_id=product_id, attribute_id=attribute_id)
        response = self.repo.create(product_attribute)

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
        product = self.repo.get_by_ids(product_id, attribute_id)

        if not product: 
            product = self.repo.create(product_id, attribute_id)

        return product
