from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class ProductValue(Base):
    __tablename__ = "product_values"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    value_id = Column(Integer, ForeignKey("values.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "value_id"),
    )

    product = relationship("Product", back_populates="product_values")
    value = relationship("Value", back_populates="product_values")
