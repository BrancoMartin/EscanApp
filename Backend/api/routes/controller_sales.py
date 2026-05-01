from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.sale_service import SaleService
from dependencies import get_sale_service
from sqlalchemy.orm import Session

router = APIRouter()

class SaleItemInput(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class SaleInput(BaseModel):
    items: list[SaleItemInput]
    

# List sale history
@router.get("/")
def get_all(service: SaleService = Depends(get_sale_service)):
    return service.get_history()

# Create a sale from item list
@router.post("/")
def create(data: SaleInput, service: SaleService = Depends(get_sale_service)):
    return service.create(data.items)

# Close a pending sale
@router.post("/{sale_id}/close")
def close_sale(sale_id: int, service: SaleService = Depends(get_sale_service)):
    print(f"Intentando cerrar venta con ID: {sale_id}")
    result = service.close_sale(sale_id)
    print("Resultado de cerrar venta:", result)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# Get sale details
@router.get("/{sale_id}")
def get_sale(sale_id: int, service: SaleService = Depends(get_sale_service)):
    sale = service.get_details(sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale

@router.put("/{sale_id}/items/{item_id}")
def handle_cancel_item_product(sale_id: int, item_id: int, service: SaleService = Depends(get_sale_service)):
    print(f"Intentando cancelar item con ID {item_id} de la venta con ID {sale_id}")
    result = service.remove_item_from_sale(sale_id, item_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
