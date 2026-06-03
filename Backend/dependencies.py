from sqlalchemy.orm import Session
from fastapi import Depends
from Backend.database import get_db
from Backend.services.product_service import ProductService
from Backend.services.sale_service import SaleService
from Backend.services.category_service import CategoryService
from Backend.services.attribute_service import AttributeService
from Backend.services.product_attribute_service import ProductAttributeService

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)

def get_sale_service(db: Session = Depends(get_db)) -> SaleService:
    return SaleService(db)

def get_category_service(db: Session = Depends(get_db)) -> CategoryService: 
    return CategoryService(db)

def get_attribute_service(db: Session = Depends(get_db)) -> AttributeService: 
    return AttributeService(db)

def get_product_attribute_service(db: Session = Depends(get_db)) -> ProductAttributeService: 
    return ProductAttributeService(db)
