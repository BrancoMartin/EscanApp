from sqlalchemy.orm import Session
from sqlalchemy import desc
from Backend.models.product_value import ProductValue
from Backend.repositories.repository_base import RepositoryBase
from typing import List

class ProductValueRepository(RepositoryBase[ProductValue]):

    def __init__(self, db: Session):
        super().__init__(db, ProductValue)
        self.db = db


