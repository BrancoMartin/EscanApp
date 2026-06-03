from sqlalchemy.orm import Session
from sqlalchemy import desc
from Backend.models.attribute import Attribute
from Backend.models.item_sale import SaleItem
from Backend.models.product import Product
from datetime import datetime
from Backend.repositories.repository_base import RepositoryBase
from typing import List


class AttributeRepository(RepositoryBase[Attribute]): 
    
    def __init__(self, db:Session): 
        super().__init__(db, Attribute)
        self.db = db

    def get_by_name_and_category_id(self, category_id, name): 
        return self.db.query(Attribute).filter(Attribute.category_id == category_id, Attribute.name == name).first()
