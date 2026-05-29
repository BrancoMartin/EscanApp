from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.value import Value
from models.item_sale import SaleItem
from models.product import Product
from datetime import datetime
from repositories.repository_base import RepositoryBase
from typing import List


class ValueRepository(RepositoryBase[Value]): 
    
    def __init__(self, db:Session): 
        super().__init__(db, Value)
        self.db = db

    def get_by_name_and_category_id(self, category_id, value): 
        return self.db.query(Value).filter(Value.category_id == category_id, Value.value == value)

  
