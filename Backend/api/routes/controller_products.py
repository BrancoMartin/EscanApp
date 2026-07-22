from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from Backend.services.product_service import ProductService
from Backend.services.product_import_service import importar_productos, ImportError400
from Backend.services.sale_service import SaleService
from Backend.models.product_attribute import ProductAttribute
from Backend.services.product_attribute_service import ProductAttributeService
from Backend.dependencies import get_product_service, get_sale_service, get_product_attribute_service
from typing import Optional
from sqlalchemy.orm import Session
# El enriquecimiento es el MISMO que usa el agente: una sola implementacion en
# la capa de servicios. La copia que vivia aca invocaba dos modelos en serie.
from Backend.services.product_enrichment_service import enriquecer_producto
from Backend.database import SessionLocal
from Backend.models.product import Product
import threading

router = APIRouter()

class ProductInput(BaseModel):
    barcode: str
    name: str
    price: float
    description: Optional[str] = None
    proveedor: Optional[str] = None


def normalizar(texto):
    """Normaliza un campo de texto: sin espacios sobrantes y en minusculas.

    Devuelve None cuando el campo esta ausente o vacio: description y proveedor
    son opcionales (la tabla products los acepta NULL), asi que llamarles
    .lower() directamente reventaba con 'NoneType' object has no attribute
    'lower' apenas el usuario creaba un producto sin descripcion.
    """
    if texto is None:
        return None
    limpio = texto.strip().lower()
    if limpio == "":
        return None
    return limpio


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

def assign_attribute_to_product(db: Session, product_id: int, attribute_id: int,  
                                product_attribute_service: ProductAttribute = Depends(get_product_attribute_service)):
    
    result = product_attribute_service.assign_attribute_to_product(product_id, attribute_id)
    if result is None: 
        print("ERROR ASIGNANDO ATRIBUTO AL PRODUCTO")
        raise HTTPException(status_code=404, detail="producto no encontrado")
    return result


def _enriquecer_en_segundo_plano(product_id: int):
    """Infiere categorias y atributos del producto FUERA del request.

    El alta ya respondio: el producto esta persistido y el usuario ya vio su
    mensaje de exito. Este hilo abre su propia sesion, porque la del request se
    cerro al responder.

    Se traga sus errores a proposito: el producto ya esta creado y el alta ya
    fue exitosa. Que Ollama este caido no puede convertirse en un problema del
    usuario despues de que la app le dijo que su producto se guardo."""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return
        asignados = enriquecer_producto(db, product)
        print(f"[PRODUCTS] Enriquecimiento de '{product.name}': {asignados} atributo(s)")
    except Exception as exc:
        print(f"[PRODUCTS] Fallo el enriquecimiento del producto {product_id}: {exc}")
    finally:
        db.close()


# Create product
@router.post("/")
def create(data: ProductInput, service: ProductService = Depends(get_product_service)):
    try:
        print("Intentando crear producto con datos:", data)

        # Se normaliza una sola vez, aca en el borde de la API. description y
        # proveedor son opcionales: quedan en None si no vinieron.
        nombre = normalizar(data.name)
        descripcion = normalizar(data.description)
        proveedor = normalizar(data.proveedor)

        # `service.create` devuelve {"success": True, "product": {...}}, no el
        # modelo (la anotacion `-> Product` del servicio miente).
        productCreate = service.create(data.barcode, nombre, data.price, descripcion, proveedor)

        # Aca el producto YA esta guardado: el alta termino. Lo que sigue
        # (inferir categorias y atributos con IA) es trabajo accesorio que el
        # usuario ni ve, y en esta maquina cuesta segundos de modelo. Antes
        # corria dentro del request, en serie y con DOS modelos: el mensaje
        # "Producto creado" tardaba ~13 s en aparecer. Ahora va a un hilo
        # daemon y la respuesta sale de inmediato.
        threading.Thread(
            target=_enriquecer_en_segundo_plano,
            args=(productCreate["product"]["id"],),
            daemon=True,
        ).start()

        return productCreate

    except ValueError as exc:
        # El alta fallo (barcode duplicado, precio invalido): no hay producto
        # que enriquecer.
        print("Error creating product:", exc)
        raise HTTPException(status_code=400, detail=str(exc))

# Import products in bulk (Excel / CSV / exports de otros POS)
@router.post("/import")
async def import_products(
    file: UploadFile = File(...),
    service: ProductService = Depends(get_product_service),
):
    """Carga masiva de productos desde un archivo Excel o CSV.

    Reusa la validacion de `ProductService.create` fila por fila: los productos
    validos se guardan y los invalidos se reportan con su numero de fila y el
    motivo, sin abortar la importacion entera (spec: product import).
    """
    contenido = await file.read()
    try:
        # El service ya trae la sesion; le paso la misma db para no abrir otra.
        resumen = importar_productos(service.db, file.filename, contenido)
    except ImportError400 as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return resumen

# Update product
@router.put("/{product_id}")
def update(product_id: int, data: ProductInput, service: ProductService = Depends(get_product_service)):
    try:
        # El precio es un float: el .lower() que habia aca hacia fallar SIEMPRE
        # este endpoint ('float' object has no attribute 'lower'), con cualquier
        # payload. Y el proveedor se aceptaba en el body pero no se guardaba.
        product = service.update(
            product_id,
            normalizar(data.barcode),
            normalizar(data.name),
            data.price,
            normalizar(data.description),
            normalizar(data.proveedor),
        )
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
