from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from Backend.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"extend_existing": True} 

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    attributes = relationship("Attribute", back_populates="category")
