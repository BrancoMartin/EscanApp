from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from Backend.services.category_service import CategoryService
from Backend.services.product_service import ProductService
from Backend.services.sale_service import SaleService
from Backend.models.product_attribute import ProductAttribute
from Backend.services.attribute_service import AttributeService
from Backend.services.product_attribute_service import ProductAttributeService
from Backend.dependencies import get_product_service, get_sale_service, get_category_service, get_attribute_service, get_product_attribute_service
from typing import Optional
from sqlalchemy.orm import Session
from Backend.agent.model_attribute_extractor import attribute_extractor
from Backend.agent.model_create_categories import create_categories
from Backend.models.category import Category
from Backend.models.attribute import Attribute

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


def texto_para_ia(valor):
    """Los modelos de IA esperan texto, no null: un campo ausente va como ''."""
    if valor is None:
        return ""
    return valor


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


# Create product
@router.post("/")
def create(data: ProductInput, service: ProductService = Depends(get_product_service), service_category: CategoryService = Depends(get_category_service),
           service_attribute: AttributeService = Depends(get_attribute_service),  service_product_attribute: ProductAttributeService = Depends(get_product_attribute_service)):
    try:
        print("Intentando crear producto con datos:", data)

        # Se normaliza una sola vez, aca en el borde de la API. description y
        # proveedor son opcionales: quedan en None si no vinieron.
        nombre = normalizar(data.name)
        descripcion = normalizar(data.description)
        proveedor = normalizar(data.proveedor)

        productCreate = service.create(data.barcode, nombre, data.price, descripcion, proveedor)

        categories = service_category.get_all()

        category_names = [cat.name.lower() if cat.name else cat.name for cat in categories]

        created_categories = create_categories(
            nombre=nombre,
            descripcion=texto_para_ia(descripcion),
            proveedor=texto_para_ia(proveedor),
            categorias_existentes=category_names
        )

        print("created_categories:", created_categories)

        categorias_nuevas = created_categories.get("categorias_nuevas", [])
        for cat_name in categorias_nuevas:
            cat = service_category.get_or_create_category(cat_name.lower())
            print(f"Categoria creada: {cat.name} (id={cat.id})")

        categories = service_category.get_all()
        category_names = [cat.name.lower() if cat.name else cat.name for cat in categories]

        # 2. Extraer atributos con IA
        result = attribute_extractor(
            nombre=nombre,
            descripcion=texto_para_ia(descripcion),
            proveedor=texto_para_ia(proveedor),
            categoria=category_names
        )

        print("attribute_extractor result:", result)

        # 3. Persistir en BD
        attributes = result if type(result) is list else result.get("atributos", [])
        print("ATTRIBUTOS en controller products", attributes)
        for attr in attributes:
            print("attr['categoria']: ", attr["categoria"])
            category = service_category.get_by_name(attr["categoria"].lower())

            if not category:
                #ACA PODRIA CREARLA EN CASO DE QUE NO EXISTA
                print(f"ERROR: Categoria '{attr['categoria'].lower()}' no encontrada")
                continue

            print("attr['valor']: ", attr["valor"])

            attribute_obj = service_attribute.get_or_create_attribute(category.id, attr["valor"].lower())
            product = service.get_by_name(nombre)
            product_attribute = service_product_attribute.get_or_create(product.id, attribute_obj.id)
            if not product_attribute:
                print(f"ERROR: No se pudo asignar atributo '{attr['valor']}' al producto '{product.name}'")
            else:
                print(f"Atributo '{attr['valor']}' asignado al producto '{product.name}'")

        return productCreate

    except ValueError as exc:
        print("Error creating product:", exc)
        raise HTTPException(status_code=400, detail=str(exc))

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
