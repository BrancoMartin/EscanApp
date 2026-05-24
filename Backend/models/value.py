from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, ForeignKey,DateTime,UniqueConstraint 
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Value(Base):
    __tablename__ = "values"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    attribute = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  
    amount_products = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("category_id", "value", name="uq_category_value"),
    )

    category = relationship("Categories", back_populates="values")
    product_values = relationship("ProductValue", back_populates="value")