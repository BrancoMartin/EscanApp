from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from services.product_service import ProductService
from services.sale_service import SaleService

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)

def get_sale_service(db: Session = Depends(get_db)) -> SaleService:
    return SaleService(db)

