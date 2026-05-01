from sqlalchemy import Column, DateTime, Integer, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    state = Column(Enum("pending", "closed", "cancelled"), default="pending")
    items = relationship("SaleItem", back_populates="sale")
