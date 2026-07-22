"""Enriquecimiento de un producto: categorias y atributos inferidos.

Vive en la capa de servicios porque lo usan los DOS caminos de alta de producto:
el formulario web (`controller_products.create`) y el chat del agente
(`controller_agent`). Antes vivia solo en el controlador del agente, y el del
formulario tenia su propia copia peor: invocaba `create_categories` Y
`attribute_extractor` siempre, en serie (12.85 s medidos en la maquina real).

Presupuesto de la maquina (i3-1115G4, 2 nucleos, sin GPU, 7.7 GB): Ollama
mantiene UN SOLO modelo residente. Dos modelos en el mismo flujo se expulsan
mutuamente y cada uno se recarga de disco. De ahi la regla: **1 modelo por
enriquecimiento**. `create_categories` solo corre como fallback, cuando
`attribute_extractor` no devolvio nada.
"""

import re

from sqlalchemy.orm import Session

from Backend.agent.model_attribute_extractor import attribute_extractor
from Backend.agent.model_create_categories import create_categories
from Backend.models.attribute import Attribute
from Backend.models.category import Category
from Backend.models.product import Product
from Backend.models.product_attribute import ProductAttribute

NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})

# Tope de categorias que se le muestran a AttributeExtractor. Cada categoria de
# mas es prompt eval (tiempo directo en CPU) y le da al 0.5b una excusa para
# inventar un atributo mas.
MAX_CATEGORIAS_PROMPT = 12


def is_valid_str(v):
    return type(v) == str and v.strip().lower() not in NULL_SYNONYMS


def normalizar(texto: str) -> str:
    """Minusculas y sin acentos, para comparar texto del usuario contra la BD."""
    t = (texto or "").strip().lower()
    for con_acento, sin_acento in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ü", "u")):
        t = t.replace(con_acento, sin_acento)
    return t


def raiz(palabra: str) -> str:
    """Raiz aproximada: saca el plural para que 'galletas' matchee 'galleta'."""
    p = normalizar(palabra)
    if len(p) > 4 and p.endswith("es"):
        return p[:-2]
    if len(p) > 3 and p.endswith("s"):
        return p[:-1]
    return p


def match_productos_por_valor(productos: list, valor: str) -> list:
    """Productos cuyo nombre o descripcion mencionan el valor del atributo.

    Va mas alla del ILIKE crudo: compara sin acentos y por raiz, asi 'galletas'
    encuentra 'Galleta rellena' y 'plastico' encuentra 'plástico'. Cuanto mejor
    resuelve esto la BD, menos veces hay que gastar el modelo."""
    raices_valor = [raiz(t) for t in re.findall(r'\w+', valor) if len(t) > 2]
    if not raices_valor:
        return []

    encontrados = []
    for p in productos:
        texto = normalizar(f"{p.name} {p.description or ''}")
        raices_texto = [raiz(t) for t in re.findall(r'\w+', texto)]
        # Todas las raices del valor tienen que aparecer en el producto: asi
        # "galletas de chocolate" no matchea cualquier producto con "chocolate".
        if all(any(rv == rt or rv in rt for rt in raices_texto) for rv in raices_valor):
            encontrados.append(p)
    return encontrados


def asignar_atributos_existentes(db: Session, product: Product) -> int:
    """Vincula el producto nuevo a los atributos que YA existen y aparecen en su
    nombre o descripcion. Deterministico, sin modelo. Es la otra mitad de
    `agregar_atributo`: si el usuario creo el atributo 'galletas' cuando todavia
    no tenia productos, el producto que cree despues lo toma solo."""
    asignados = 0
    for a in db.query(Attribute).all():
        if not match_productos_por_valor([product], a.name):
            continue
        existe = db.query(ProductAttribute).filter_by(product_id=product.id, attribute_id=a.id).first()
        if not existe:
            db.add(ProductAttribute(product_id=product.id, attribute_id=a.id))
            asignados += 1
    if asignados:
        db.commit()
    return asignados


def enriquecer_producto(db: Session, product: Product) -> int:
    """Asigna al producto sus categorias y atributos. Devuelve cuantos vinculo.

    Gasta COMO MAXIMO un modelo: `attribute_extractor`. `create_categories` solo
    entra si el extractor no devolvio nada."""
    proveedor = product.proveedor or ""

    # Primero lo que la BD ya sabe (sin modelo): atributos existentes que el
    # producto menciona en su nombre o descripcion.
    asignar_atributos_existentes(db, product)

    # Si el proveedor viene informado, la categoria "proveedor" debe existir ANTES
    # de extraer atributos, para que AttributeExtractor devuelva el atributo de
    # proveedor (SDD ai-agent). Que la categoria se llama "proveedor" ya lo
    # sabemos: no hace falta preguntarselo a un modelo. Lo hacemos deterministico
    # y nos ahorramos una llamada a CreateCategories (~1.5s) en cada creacion.
    if is_valid_str(proveedor):
        existe_cat = db.query(Category).filter(Category.name == "proveedor").first()
        if not existe_cat:
            db.add(Category(name="proveedor"))
            db.commit()

    # Acotamos las categorias que ve el modelo: cuantas mas le pasamos, mas
    # atributos inventa (emitia uno por categoria), agotando num_predict. La
    # categoria "proveedor" tiene que estar si el proveedor vino informado.
    cats = db.query(Category).all()
    cats_list = [c.name for c in cats][:MAX_CATEGORIAS_PROMPT]
    if is_valid_str(proveedor) and "proveedor" not in cats_list:
        cats_list.append("proveedor")

    # OJO: AttributeExtractor espera la lista de categorias (no un string),
    # para poder agregar el proveedor de forma deterministica.
    atributos_extra = attribute_extractor(product.name, product.description or "", cats_list, proveedor)

    # Fallback: si el extractor no infirio ningun atributo, pedimos a
    # CreateCategories que bootstrapee categorias para los proximos productos.
    if not atributos_extra:
        nuevas = create_categories(product.name, product.description or "", proveedor, cats_list)
        for nombre_cat in nuevas.get("categorias_nuevas", []):
            if is_valid_str(nombre_cat):
                existe_cat = db.query(Category).filter(Category.name == nombre_cat).first()
                if not existe_cat:
                    db.add(Category(name=nombre_cat))
        db.commit()
        return 0

    contados = 0
    for attr in atributos_extra:
        cat_name = attr.get("categoria")
        val = attr.get("valor")
        if not is_valid_str(cat_name) or not is_valid_str(val):
            continue
        ac = db.query(Category).filter(Category.name == cat_name).first()
        if not ac:
            ac = Category(name=cat_name)
            db.add(ac)
            db.commit()
            db.refresh(ac)
        av = db.query(Attribute).filter(
            Attribute.category_id == ac.id,
            Attribute.name == val
        ).first()
        if not av:
            av = Attribute(category_id=ac.id, name=val)
            db.add(av)
            db.commit()
            db.refresh(av)
        existe = db.query(ProductAttribute).filter_by(product_id=product.id, attribute_id=av.id).first()
        if not existe:
            db.add(ProductAttribute(product_id=product.id, attribute_id=av.id))
            contados += 1
    if contados:
        db.commit()
    return contados
