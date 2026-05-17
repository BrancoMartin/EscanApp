from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# models/category.py
from models.association_tables import product_category

class Values(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String, nullable=False, index=True)

    attributes = relationship("Attribute", back_populates="category")  # esto es one-to-many
