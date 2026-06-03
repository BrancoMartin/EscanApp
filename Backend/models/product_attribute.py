from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from Backend.database import Base

class ProductAttribute(Base):
    __tablename__ = "product_attributes"
    __table_args__ = (
        UniqueConstraint("product_id", "attribute_id"),
        {"extend_existing": True}
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    attribute_id = Column(Integer, ForeignKey("attributes.id"), nullable=False)

    product = relationship("Product", back_populates="product_attributes")
    attribute = relationship("Attribute", back_populates="product_attributes")
