from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from models.association_tables import product_attribute

class Attribute(Base):
    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    attribute = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  
    amount_products = Column(Integer, nullable=False, default=0)

    category = relationship("Category", back_populates="attributes")
    products = relationship("Product", secondary=product_attribute, back_populates="attributes")