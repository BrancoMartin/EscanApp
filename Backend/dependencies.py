from sqlalchemy.orm import Session
from fastapi import Depends
from Backend.database import get_db
from Backend.services.product_service import ProductService
from Backend.services.sale_service import SaleService
from Backend.services.category_service import CategoryService
from Backend.services.value_service import ValueService
from Backend.services.product_value_service import ProductValueService

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)

def get_sale_service(db: Session = Depends(get_db)) -> SaleService:
    return SaleService(db)

def get_category_service(db: Session = Depends(get_db)) -> CategoryService: 
    return CategoryService(db)

def get_value_service(db: Session = Depends(get_db)) -> ValueService: 
    return ValueService(db)

def get_product_value_service(db: Session = Depends(get_db)) -> ProductValueService: 
    return ProductValueService(db)