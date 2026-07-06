from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from Backend.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    proveedor = Column(String, nullable=True, default=None)
    price = Column(Float, nullable=False)
    barcode = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    sale_items = relationship("SaleItem", back_populates="product")

    product_attributes = relationship("ProductAttribute", back_populates="product")

    
