from sqlalchemy.orm import Session
from Backend.repositories.category_repository import CategoryRepository
from Backend.models.category import Category
from typing import List
from datetime import date


class CategoryService: 

    def __init__(self, db:Session): 
        self.db = db
        self.repo = CategoryRepository(db)

    def get_all(self) -> List[Category]:
        return self.repo.get_all()
    
    def get_by_id(self, product_id: int) -> Category:
        category = self.repo.get_by_id(product_id)
        if not category:
            raise ValueError("Product not found")
        return category
    
    def create(self, name) -> Category:
        if not name or name.strip() == "":
            raise ValueError("El nombre es obligatorio")
       
        created_at = date.today()
       
        category = Category(name=name, created_at=created_at)
        response = self.repo.create(category)

        return {
    "success": True,
    "category": {
        "id": response.id,
        "name": response.name,
        "created_at": response.created_at
    }}



    def update(self, id, name) -> Category:

        if not name or name.strip() == "":
            raise ValueError("El nombre es obligatorio")
        
        category = self.get_by_id(id)

        if not category: 
            raise FileNotFoundError("categoria no encontrada")
        
       
        category.name = name
    
        response = self.repo.update(category)

        return {
    "success": True,
    "category": {
        "id": response.id,
        "name": response.name,
        "created_at": response.created_at
    }}


    def delete(self, categroy_id: int) -> bool:
        return self.repo.delete(categroy_id)
    
    def get_by_name(self, name_category):
        category = self.repo.get_by_name(name_category)

        return category


    def get_or_create_category(self, name_category): 

        category = self.get_by_name(name_category)

        if not category: 
            created = self.create(name_category)
            if type(created) == dict:
                return self.repo.get_by_id(created["category"]["id"])
            return created

        return category
        