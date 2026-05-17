from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class AttributeValue(Base):
    __tablename__ = "attribute_values"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("attribute_categories.id"), nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("category_id", "value", name="uq_category_value"),
    )

    category = relationship("AttributeCategory", back_populates="values")
    product_links = relationship("ProductAttributeBridge", back_populates="attribute_value")
