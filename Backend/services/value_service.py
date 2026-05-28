from sqlalchemy.orm import Session
from repositories.value_repository import ValueRepository
from models.value import Value
from typing import List
from datetime import date
from services.product_service import ProductService


class ValueService: 
    def __init__(self, db:Session): 
        self.product = ProductService()

    def get_all(self) -> List[Value]:
        return self.repo.get_all()
    
    def get_by_id(self, product_id: int) -> Value:
        value = self.repo.get_by_id(product_id)
        if not value:
            raise ValueError("Product not found")
        return value
    
    def create(self, name, category_id) -> Value:
        if not name or name.strip() == "":
            raise ValueError("El nombre es obligatorio")
       
        
       
        value = Value(value=name, category_id=category_id)
        response = self.repo.create(value)

        return {
    "success": True,
    "value": {
        "id": response.id,
        "name": response.name,
        "created_at": response.created_at
    }}



    def update(self, id, name) -> Value:

        if not name or name.strip() == "":
            raise ValueError("El nombre es obligatorio")
        
        value = self.get_by_id(id)

        if not value: 
            raise FileNotFoundError("categoria no encontrada")
        
        amount_product = len(self.product.get_product_by_value(value.id))
       
        value.name = name
    
        response = self.repo.update(value)

        return {
    "success": True,
    "value": {
        "id": response.id,
        "name": response.name,
        "created_at": response.created_at
    }}


    def delete(self, categroy_id: int) -> bool:
        return self.repo.delete(categroy_id)
    