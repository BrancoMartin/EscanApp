from sqlalchemy.orm import Session
from models.category import Category
from repositories.repository_base import RepositoryBase

class CategoryRepository(RepositoryBase[Category]): 

    def __init__(self, db, Session): 
        super().__init__(db, Category)
        self.db = db

        def get_by_name(self, name): 
            return self.db.query(Category).filter(Category.name == name).first()