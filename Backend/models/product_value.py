from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from Backend.database import Base

class ProductValue(Base):
    __tablename__ = "product_values"
    __table_args__ = (
        UniqueConstraint("product_id", "value_id"),
        {"extend_existing": True}
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    value_id = Column(Integer, ForeignKey("values.id"), nullable=False)

    product = relationship("Product", back_populates="product_values")
    value = relationship("Value", back_populates="product_values")
