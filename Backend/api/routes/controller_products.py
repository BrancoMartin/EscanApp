from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from Backend.services.category_service import CategoryService
from Backend.services.product_service import ProductService
from Backend.services.sale_service import SaleService
from Backend.models.product_value import ProductValue
from Backend.services.value_service import ValueService
from Backend.services.product_value_service import ProductValueService
from Backend.dependencies import get_product_service, get_sale_service, get_category_service, get_value_service, get_product_value_service
from typing import Optional
from sqlalchemy.orm import Session
from Backend.agent.model_value_extractor import value_extractor
from Backend.agent.model_create_categories import create_categories
from Backend.models.category import Category
from Backend.models.value import Value

router = APIRouter()

class ProductInput(BaseModel):
    barcode: str
    name: str
    price: float
    description: Optional[str] = None

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
    result = sale_service.scan_product_by_barcode(barcode)
    if result is None:
        print("ERROR ESCANEANDO PRODUCTO: Producto no encontrado")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return result

def assign_attribute_to_product(db: Session, product_id: int, value_id: int):
    exists = db.query(ProductValue).filter_by(
        product_id=product_id,
        value_id=value_id
    ).first()
    if not exists:
        pa = ProductValue(product_id=product_id, value_id=value_id)
        db.add(pa)
        db.commit()

# Create product
@router.post("/")
def create(data: ProductInput, service: ProductService = Depends(get_product_service), service_category: CategoryService = Depends(get_category_service),
           service_value: ValueService = Depends(get_value_service),  service_product_value: ProductValueService = Depends(get_product_value_service)):
    try:
        print("Intentando crear producto con datos:", data)
        productCreate = service.create(data.barcode, data.name, data.price, data.description)

        categories = service_category.get_all()

        created_categories = create_categories(
            nombre=data.name,
            descripcion=data.description,
            proveedor=None,
            categoria=categories
        )
    
            # 2. Extraer atributos con IA
        result = value_extractor(
            nombre=data.name,
            descripcion=data.description,
            proveedor=None,
            categoria=categories
        )

        print(result)

        # 3. Persistir en BD
        values = result.get("atributos", [])
        for val in values:
            category = service_category.get_or_create_category(val["categoria"])
            value_obj = service_value.get_or_create_value(category.id, val["valor"])
            product = service.get_by_name(data.name)
            product_value = service_product_value.get_or_create(product.id, value_obj.id)

        return productCreate

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

