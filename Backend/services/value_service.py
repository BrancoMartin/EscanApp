from sqlalchemy.orm import Session
from Backend.repositories.value_repository import ValueRepository
from Backend.models.value import Value
from typing import List
from datetime import date
from Backend.services.product_service import ProductService


class ValueService: 
    def __init__(self, db:Session): 
        self.product = ProductService(db)
        self.repo = ValueRepository(db)

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
       
        if not category_id: 
            raise ValueError("el id de la categoria no esta")
        
        created_at = date.today()
       
        value = Value(value=name, category_id=category_id, created_at=created_at)
        response = self.repo.create(value)

        return {
        "success": True,
        "value": {
        "id": response.id,
        "name": response.value,
        "created_at": response.created_at
    }}



    def update(self, id, name) -> Value:

        if not name or name.strip() == "":
            raise ValueError("El nombre es obligatorio")
        
        value = self.get_by_id(id)

        if not value: 
            raise FileNotFoundError("categoria no encontrada")
        
        amount_product = len(self.product.get_product_by_value(value.id))
       
        value.value = name
        value.amount_products = amount_product
    
        response = self.repo.update(value)

        return {
    "success": True,
    "value": {
        "id": response.id,
        "name": response.value,
        "created_at": response.created_at
    }}


    def delete(self, categroy_id: int) -> bool:
        return self.repo.delete(categroy_id)
    

    def get_by_name_and_category_id(self, category_id, value_name): 
        return self.repo.get_by_name_and_category_id(category_id, value_name)

    def get_or_create_value(self, category_id, value_name): 
        existing = self.get_by_name_and_category_id(category_id, value_name)

        if not existing: 
            created = self.create(value_name, category_id)
            if isinstance(created, dict):
                return self.repo.get_by_id(created["value"]["id"])
            return created

        return existing
        