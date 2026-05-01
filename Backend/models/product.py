from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from database import Base
# models/product.py
from models.association_tables import product_attribute, product_category

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    barcode = Column(String, unique=True, nullable=False, index=True)

    attributes = relationship("Attribute", secondary=product_attribute, back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
