from sqlalchemy.orm import Session
from Backend.repositories.product_value_repository import ProductValueRepository
from Backend.repositories.product_repository import ProductRepository
from Backend.models.product_value import ProductValue
from typing import List



class ProductValueService: 

    def __init__(self, db: Session):
        self.repo = ProductValueRepository(db)
        self.product = ProductRepository(db)

    def get_all(self) -> List[ProductValue]:
        return self.repo.get_all()
    
    
    def create(self, product_id, value_id) -> ProductValue:
        if not product_id:
            raise ValueError("El product id es obligatorio")
       
        if not value_id: 
            raise ValueError("el id del value no esta")
       
        product_value = ProductValue(product_id=product_id, value_id=value_id)
        response = self.repo.create(product_value)

        return {
    "success": True,
    "value": {
        "product_id":product_id, 
        "value_id":value_id
    }}


    def get_by_name(self, name): 
        product = self.repo.get_by_name(name)
        return product

    
    def get_or_create(self, product_id, value_id): 
        product = self.repo.get_by_ids(product_id, value_id)

        if not product: 
            product = self.repo.create(product_id, value_id)

        return product
            
