from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from Backend.database import Base
# models/product.py


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    barcode = Column(String, unique=True, nullable=False, index=True)

    sale_items = relationship("SaleItem", back_populates="product")

    product_values = relationship("ProductValue", back_populates="product")

    