from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, ForeignKey, DateTime, UniqueConstraint 
from sqlalchemy.orm import relationship
from Backend.database import Base
from datetime import datetime

class Attribute(Base):
    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  
    amount_products = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_category_attribute"),
    )

    category = relationship("Category", back_populates="attributes")
    product_attributes = relationship("ProductAttribute", back_populates="attribute")
