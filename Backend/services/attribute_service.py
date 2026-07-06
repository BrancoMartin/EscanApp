from sqlalchemy.orm import Session
from Backend.repositories.attribute_repository import AttributeRepository
from Backend.models.attribute import Attribute
from typing import List
from datetime import date
from Backend.services.product_service import ProductService


class AttributeService: 
    def __init__(self, db:Session): 
        self.product = ProductService(db)
        self.repo = AttributeRepository(db)

    def get_all(self) -> List[Attribute]:
        return self.repo.get_all()
    
    def get_by_id(self, attribute_id: int) -> Attribute:
        attribute = self.repo.get_by_id(attribute_id)
        if not attribute:
            raise ValueError("Attribute not found")
        return attribute
    
    def create(self, name, category_id) -> Attribute:
        if not name or name.strip() == "":
            raise ValueError("El nombre es obligatorio")
       
        if not category_id: 
            raise ValueError("el id de la categoria no esta")
        
        created_at = date.today()
       
        attribute = Attribute(name=name, category_id=category_id, created_at=created_at)
        response = self.repo.create(attribute)

        return {
        "success": True,
        "attribute": {
        "id": response.id,
        "name": response.name,
        "created_at": response.created_at
    }}



    def update(self, id, name) -> Attribute:

        if not name or name.strip() == "":
            raise ValueError("El nombre es obligatorio")
        
        attribute = self.get_by_id(id)

        if not attribute: 
            raise FileNotFoundError("atributo no encontrado")
        
        amount_product = len(self.product.get_product_by_attribute(attribute.id))
       
        attribute.name = name
        attribute.amount_products = amount_product
    
        response = self.repo.update(attribute)

        return {
    "success": True,
    "attribute": {
        "id": response.id,
        "name": response.name,
        "created_at": response.created_at
    }}


    def delete(self, category_id: int) -> bool:
        return self.repo.delete(category_id)
    

    def get_by_name_and_category_id(self, category_id, attribute_name): 
        return self.repo.get_by_name_and_category_id(category_id, attribute_name)

    def get_by_name(self, name):
        return self.repo.get_by_name(name)

    def get_or_create_attribute(self, category_id, attribute_name): 
        existing = self.get_by_name_and_category_id(category_id, attribute_name)

        if not existing: 
            created = self.create(attribute_name, category_id)
            if type(created) == dict:
                return self.repo.get_by_id(created["attribute"]["id"])
            return created

        return existing
