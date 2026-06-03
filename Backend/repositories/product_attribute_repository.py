from sqlalchemy.orm import Session
from sqlalchemy import desc
from Backend.models.product_attribute import ProductAttribute
from Backend.repositories.repository_base import RepositoryBase
from typing import List

class ProductAttributeRepository(RepositoryBase[ProductAttribute]):

    def __init__(self, db: Session):
        super().__init__(db, ProductAttribute)
        self.db = db


    def get_by_ids(self, product_id, attribute_id):
        return self.db.query(ProductAttribute).filter(
            ProductAttribute.product_id == product_id,
            ProductAttribute.attribute_id == attribute_id
        ).first()
