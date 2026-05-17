from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class ProductAttributeBridge(Base):
    __tablename__ = "product_attributes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    attribute_value_id = Column(Integer, ForeignKey("attribute_values.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "attribute_value_id", name="uq_product_attribute_value"),
    )

    product = relationship("Product")
    attribute_value = relationship("AttributeValue", back_populates="product_links")
