from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.product_service import ProductService
from services.sale_service import SaleService
from dependencies import get_product_service, get_sale_service
from services.ai_price_service import AIPriceService
from sqlalchemy.orm import Session
router = APIRouter()

class ProductInput(BaseModel):
    barcode: str
    name: str
    price: float
    description: str | None = None

# List all products
@router.get("/")
def get_all(service: ProductService = Depends(get_product_service)):
    return service.get_all()

# Get by barcode (used by the scanner)
@router.get("/barcode/{barcode}")
def get_by_barcode(
    barcode: str,
    sale_service: SaleService = Depends(get_sale_service)
):
    try:
        result = sale_service.scan_product_by_barcode(barcode)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return result

# Create product
@router.post("/")
def create(data: ProductInput, service: ProductService = Depends(get_product_service)):
    try:
        print("Intentando crear producto con datos:", data)
        return service.create(data.barcode, data.name, data.price, data.description)
    except ValueError as exc:
        print("Error creating product:", exc)
        raise HTTPException(status_code=400, detail=str(exc))

# Update product
@router.put("/{product_id}")
def update(product_id: int, data: ProductInput, service: ProductService = Depends(get_product_service)):
    try:
        product = service.update(product_id, data.barcode, data.name, data.price, data.description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Delete product
@router.delete("/{product_id}")
def delete(product_id: int, service: ProductService = Depends(get_product_service)):
    service.delete(product_id)
    return {"message": "Product deleted"}

@router.get("/{attribute_id}")
def get_products_by_attribute(attribute_id: int, service: ProductService = Depends(get_product_service)):
    result = service.get_products_by_attribute(attribute_id)
    return {"message": result}

