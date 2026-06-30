from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Backend.database import get_db
from Backend.models.product import Product

router = APIRouter()

class StockInput(BaseModel):
    quantity: int

@router.get("/{product_id}")
def get_stock(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"product_id": product.id, "name": product.name, "stock": product.stock or 0}

@router.put("/{product_id}")
def update_stock(product_id: int, data: StockInput, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.stock = data.quantity
    db.commit()
    return {"product_id": product.id, "name": product.name, "stock": product.stock}

@router.post("/{product_id}/add")
def add_stock(product_id: int, data: StockInput, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.stock = (product.stock or 0) + data.quantity
    db.commit()
    return {"product_id": product.id, "name": product.name, "stock": product.stock}
