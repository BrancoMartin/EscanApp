from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session
from Backend.database import get_db
from Backend.models.category import Category
from Backend.models.attribute import Attribute
from Backend.models.product_attribute import ProductAttribute
from Backend.models.product import Product
from dotenv import load_dotenv
import os
import re

from Backend.agent.model1_intent import detect_intent
from Backend.agent.model2a_create_product import create_product_with_attributes
from Backend.agent.model2b_price_type import detect_price_increase_type
from Backend.agent.model3_detect_attr import detect_category_and_value
from Backend.agent.model5_incomplete import handle_incomplete_info
from Backend.agent.model6_general import handle_general_query
from Backend.agent.model4_resolve_attr import resolve_attribute_in_db
from Backend.agent.model_attribute_extractor import attribute_extractor
from Backend.agent.model_create_categories import create_categories
from Backend.services.attribute_service import AttributeService

load_dotenv()

router = APIRouter()


_NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})

def _is_valid_str(v):
    return type(v) == str and v.strip().lower() not in _NULL_SYNONYMS


_UNIDADES = r'(?:unidad|unidades|litro|litros|kilo|kilos|kg|gramo|gramos|gr|ml|cc|cm|metro|metros|docena|pack)'

def _parse_producto_deterministico(msg: str) -> dict:
    """Extrae de forma deterministica nombre/precio/barcode/proveedor del mensaje.
    Solo devuelve los campos que aparecen EXPLICITOS; el resto lo completa el
    modelo o el flujo conversacional. Evita depender del modelo 0.5b para datos
    que el usuario escribio literalmente (mismo criterio que ajuste de precios y
    agregar_atributo)."""
    data: dict = {}
    texto = msg.strip()

    # 1) barcode: primera secuencia de 6+ digitos
    m_bc = re.search(r'\b(\d{6,})\b', texto)
    if m_bc:
        data["barcode"] = m_bc.group(1)

    # 2) proveedor: "proveedor X" hasta un marcador o fin
    m_pv = re.search(r'proveedor(?:es)?\s+(?:de\s+|del\s+)?(.+?)(?:\s+(?:precio|vale|sale|cuesta|codigo|barcode|a\s+\$?\d|\$\d|\d{3,})|\s*$)', texto, re.IGNORECASE)
    if m_pv and m_pv.group(1).strip():
        data["proveedor"] = m_pv.group(1).strip(' .,;:')

    # 3) precio: marcadores explicitos primero; si no, numero suelto (no cantidad)
    precio = None
    lone_token = None
    for pat in [
        r'\$\s*(\d+(?:[.,]\d+)?)',
        r'(?:precio|vale|sale|cuesta)\s*:?\s*\$?\s*(\d+(?:[.,]\d+)?)',
        r'\ba\s+\$?\s*(\d+(?:[.,]\d+)?)\b',
        r'(\d+(?:[.,]\d+)?)\s*(?:pesos|ars)',
    ]:
        m = re.search(pat, texto, re.IGNORECASE)
        if m:
            precio = m.group(1)
            break
    if precio is None:
        bc = data.get("barcode", "")
        for m in re.finditer(r'\b(\d{1,5}(?:[.,]\d+)?)\b', texto):
            n = m.group(1)
            if bc and n in bc:
                continue
            resto = texto[m.end():].lstrip()
            if re.match(_UNIDADES + r'\b', resto, re.IGNORECASE):
                continue  # es cantidad, no precio
            precio = n
            lone_token = n
            break
    if precio is not None:
        try:
            data["precio"] = float(precio.replace(",", "."))
        except ValueError:
            pass

    # 4) nombre: texto tras "producto/articulo"
    m_nb = re.search(r'(?:producto|articulo|artículo)s?\s*:?\s+(.+)', texto, re.IGNORECASE)
    if m_nb:
        nombre = m_nb.group(1)
        nombre = re.sub(r'^(?:nuevo\s+|nueva\s+|un\s+|una\s+|el\s+|la\s+|llamado\s+|llamada\s+|que\s+se\s+llame\s+)+', '', nombre, flags=re.IGNORECASE)
        nombre = re.split(r'\s+(?:a\s+\$?\d|\$\s*\d|precio|vale|sale|cuesta|proveedor|codigo|barcode|de\s+\$?\d|\d{3,})', nombre, maxsplit=1, flags=re.IGNORECASE)[0]
        # si el precio vino de un numero suelto, quitarlo si quedo al final del nombre
        if lone_token:
            nombre = re.sub(r'[\s,]*\b' + re.escape(lone_token) + r'\b\s*$', '', nombre)
        nombre = nombre.strip(' .,;:"\'').strip()
        if nombre:
            data["nombre"] = nombre
    return data


def _limpiar_nombre_categoria(raw) -> str:
    """Normaliza el nombre de categoria extraido del mensaje: quita fillers
    ('llamada', 'nueva', articulos, 'de'), corta clausulas finales y comillas."""
    if not _is_valid_str(raw):
        return ""
    nombre = raw.strip()
    nombre = re.sub(r'^(?:llamada\s+|llamado\s+|nueva\s+|nuevo\s+|de\s+|una\s+|un\s+|la\s+|el\s+|los\s+|las\s+|que\s+se\s+llame\s+)+', '', nombre, flags=re.IGNORECASE)
    nombre = re.split(r'\s+(?:para\s+|que\s+|con\s+|y\s+|asignal\w*|asigna\w*)', nombre, maxsplit=1, flags=re.IGNORECASE)[0]
    nombre = nombre.strip(' .,;:!?"\'“”‘’').strip()
    return nombre


def _limpiar_token(s) -> str:
    """Quita articulos iniciales y puntuacion de un nombre extraido."""
    if not _is_valid_str(s):
        return ""
    s = s.strip()
    s = re.sub(r'^(?:el\s+|la\s+|los\s+|las\s+|un\s+|una\s+)+', '', s, flags=re.IGNORECASE)
    return s.strip(' .,;:!?"\'“”‘’').strip()


def _parse_asignar_producto_atributo(msg: str):
    """Detecta 'asigna/vincula el producto X al atributo/categoria Y' (cualquier
    orden). Devuelve {'producto': X, 'target': Y} o None. El 'target' puede ser un
    atributo o una categoria (el usuario a veces los confunde); quien lo resuelve
    decide. Requiere la palabra 'producto', un target (atributo|categoria) y un
    verbo de asignacion, para no pisar otras acciones."""
    low = msg.lower()
    if "producto" not in low:
        return None
    if not ("atributo" in low or "categoria" in low or "categoría" in low):
        return None
    if not re.search(r'\b(asign\w*|vincul\w*|relacion\w*|añad\w*|anad\w*|liga\w*|met\w*|pon\w*)', msg, re.IGNORECASE):
        return None
    target_kw = r'(?:atributo|categoria|categoría)'
    conector = r'(?:al|a\s+el|a\s+la|con\s+el|con\s+la|en\s+el|en\s+la|del|de\s+la)?'
    m = re.search(r'producto\s+(.+?)\s+' + conector + r'\s*' + target_kw + r'\s+(.+?)\s*$', msg, re.IGNORECASE)
    if m:
        return {"producto": _limpiar_token(m.group(1)), "target": _limpiar_token(m.group(2))}
    m = re.search(target_kw + r'\s+(.+?)\s+' + conector + r'\s*producto\s+(.+?)\s*$', msg, re.IGNORECASE)
    if m:
        return {"producto": _limpiar_token(m.group(2)), "target": _limpiar_token(m.group(1))}
    return None


_pending_products: dict = {}

def save_pending_product(session_id: str, product_data: dict):
    _pending_products[session_id] = product_data

def get_pending_product(session_id: str) -> dict | None:
    return _pending_products.get(session_id)

def clear_pending_product(session_id: str):
    _pending_products.pop(session_id, None)


def _enriquecer_producto_con_atributos(db: Session, product: Product, user_message: str = ""):
    proveedor = product.proveedor or ""

    # Si el proveedor viene informado, aseguramos que exista la categoria
    # "proveedor" (y otras inferibles) ANTES de extraer atributos, para que
    # AttributeExtractor pueda devolver el atributo de proveedor (SDD ai-agent).
    if _is_valid_str(proveedor):
        cats_actuales = [c.name for c in db.query(Category).all()]
        nuevas = create_categories(product.name, product.description or "", proveedor, cats_actuales)
        for nombre_cat in nuevas.get("categorias_nuevas", []):
            if _is_valid_str(nombre_cat):
                existe_cat = db.query(Category).filter(Category.name == nombre_cat).first()
                if not existe_cat:
                    db.add(Category(name=nombre_cat))
        db.commit()

    cats = db.query(Category).all()
    cats_list = [c.name for c in cats]
    # OJO: AttributeExtractor espera la lista de categorias (no un string),
    # para poder agregar el proveedor de forma deterministica.
    atributos_extra = attribute_extractor(product.name, product.description or "", cats_list, proveedor)
    if not atributos_extra:
        return 0
    contados = 0
    for attr in atributos_extra:
        cat_name = attr.get("categoria")
        val = attr.get("valor")
        if not _is_valid_str(cat_name) or not _is_valid_str(val):
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


class ChatMessage(BaseModel):
    message: str
    conversation_history: list = []
    context: dict = {}


class AgentResponse(BaseModel):
    message: str
    action_executed: str | None = None
    success: bool = True
    data: dict = {}


_NEGATIVOS = {
    "no", "no.", "nop", "nel", "nada", "ninguno", "ninguna", "ningun", "ningún",
    "sin", "-", "n/a", "na", "skip", "omitir", "paso", "salta", "saltar",
    "sin descripcion", "sin descripción", "sin proveedor", "no tiene",
    "no gracias", "tampoco", "no quiero", "asi esta bien", "así está bien"
}

def _es_negativo(resp) -> bool:
    """True si la respuesta del usuario significa 'no' / 'omitir este dato'."""
    if not _is_valid_str(resp):
        return True
    r = resp.strip().lower().rstrip('.!¡¿?')
    return r == "" or r in _NEGATIVOS


def _crear_producto_desde_data(db: Session, product_data: dict) -> AgentResponse:
    """Crea el Product a partir de product_data ya completo (nombre, precio,
    barcode; descripcion/proveedor opcionales) y asigna sus atributos."""
    nombre = product_data.get("nombre")
    existing = db.query(Product).filter(Product.barcode == product_data["barcode"]).first()
    if existing:
        clear_pending_product("default")
        return AgentResponse(
            message=f"Ya existe un producto con ese codigo de barras: {existing.name}",
            action_executed="crear_producto",
            success=False
        )

    product = Product(
        name=nombre,
        price=float(product_data["precio"]),
        barcode=product_data["barcode"],
        description=product_data.get("descripcion"),
        proveedor=product_data.get("proveedor")
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    atributos_inf = product_data.get("atributos_inferidos", [])
    if atributos_inf:
        for attr in atributos_inf:
            cat_name = attr.get("categoria")
            val = attr.get("valor")
            if _is_valid_str(cat_name) and _is_valid_str(val):
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
                db.add(ProductAttribute(product_id=product.id, attribute_id=av.id))
        db.commit()

    extras = _enriquecer_producto_con_atributos(db, product)
    if extras:
        print(f"[ENRIQUECER] {extras} atributos adicionales asignados a '{nombre}'")

    clear_pending_product("default")
    partes = [f"Producto '{nombre}' creado exitosamente!"]
    if _is_valid_str(product.description):
        partes.append(f"Descripcion: {product.description}")
    if _is_valid_str(product.proveedor):
        partes.append(f"Proveedor: {product.proveedor}")
    return AgentResponse(
        message="\n".join(partes),
        action_executed="crear_producto",
        success=True,
        data={"id": product.id, "name": product.name, "price": product.price, "barcode": product.barcode}
    )


def _avanzar_creacion_producto(db: Session, product_data: dict) -> AgentResponse:
    """Pide el proximo dato faltante del producto (nombre -> precio ->
    descripcion -> proveedor -> barcode) o, si ya estan todos, lo crea.
    Las descripciones y el proveedor son opcionales pero SIEMPRE se preguntan
    (una vez), marcandose con _desc_ok / _prov_ok cuando el usuario responde."""
    nombre = product_data.get("nombre")
    if not _is_valid_str(nombre):
        save_pending_product("default", product_data)
        return AgentResponse(
            message="¿Que nombre tiene el producto?",
            action_executed="crear_producto",
            success=False,
            data={"product_data": product_data, "awaiting": "nombre"}
        )
    if product_data.get("precio") is None:
        save_pending_product("default", product_data)
        return AgentResponse(
            message=f"Producto: {nombre}\n\n¿Que precio tiene?",
            action_executed="crear_producto",
            success=True,
            data={"product_data": product_data, "awaiting": "precio"}
        )
    if not product_data.get("_desc_ok"):
        save_pending_product("default", product_data)
        return AgentResponse(
            message="¿Querés agregarle una descripción? Escribila, o poné 'no'.",
            action_executed="crear_producto",
            success=True,
            data={"product_data": product_data, "awaiting": "descripcion"}
        )
    if not product_data.get("_prov_ok"):
        save_pending_product("default", product_data)
        return AgentResponse(
            message="¿Tiene proveedor? Escribí el nombre del proveedor, o poné 'no'.",
            action_executed="crear_producto",
            success=True,
            data={"product_data": product_data, "awaiting": "proveedor"}
        )
    if not _is_valid_str(product_data.get("barcode")):
        save_pending_product("default", product_data)
        return AgentResponse(
            message=f"Datos del producto:\nNombre: {nombre}\nPrecio: ${product_data.get('precio')}\n\nAhora escaneá o ingresá el codigo de barras.",
            action_executed="crear_producto",
            success=True,
            data={"product_data": product_data, "awaiting": "barcode"}
        )
    return _crear_producto_desde_data(db, product_data)


@router.post("/chat", response_model=AgentResponse)
def agent_chat(chat_msg: ChatMessage, db: Session = Depends(get_db)):
    try:
        user_message = chat_msg.message
        conversation_history = chat_msg.conversation_history or []
        context = chat_msg.context or {}

        # --- Si hay un producto pendiente (creacion en curso), 
        #      NO clasificamos intent — seguimos el flujo de creacion ---
        pending = get_pending_product("default")
        if pending is not None:
            pd = pending
            resp = user_message.strip()

            # Maquina de estados: llenamos el PRIMER dato faltante con la
            # respuesta del usuario. Orden: nombre -> precio -> descripcion ->
            # proveedor -> barcode. Descripcion y proveedor son opcionales
            # (se aceptan o se omiten con 'no').
            if not _is_valid_str(pd.get("nombre")):
                if not resp or re.match(r"^\d+$", resp):
                    save_pending_product("default", pd)
                    return AgentResponse(
                        message="¿Que nombre tiene el producto?",
                        action_executed="crear_producto",
                        success=False,
                        data={"product_data": pd, "awaiting": "nombre"}
                    )
                pd["nombre"] = resp
            elif pd.get("precio") is None:
                precio_match = re.search(r'(\d+[\.,]?\d*)', user_message)
                if not precio_match:
                    save_pending_product("default", pd)
                    return AgentResponse(
                        message=f"Producto: {pd.get('nombre')}\n\nNo entendi el precio. ¿Podes decirme el valor numerico?",
                        action_executed="crear_producto",
                        success=False,
                        data={"product_data": pd, "awaiting": "precio"}
                    )
                pd["precio"] = float(precio_match.group(1).replace(",", "."))
            elif not pd.get("_desc_ok"):
                pd["descripcion"] = None if _es_negativo(resp) else resp
                pd["_desc_ok"] = True
            elif not pd.get("_prov_ok"):
                pd["proveedor"] = None if _es_negativo(resp) else resp
                pd["_prov_ok"] = True
            elif not _is_valid_str(pd.get("barcode")):
                if re.match(r"^\d+$", resp):
                    pd["barcode"] = resp
                else:
                    bc_match = re.search(r'\b(\d{6,})\b', user_message)
                    if bc_match:
                        pd["barcode"] = bc_match.group(1)
                    else:
                        save_pending_product("default", pd)
                        return AgentResponse(
                            message=f"Datos del producto:\nNombre: {pd.get('nombre')}\nPrecio: ${pd.get('precio')}\n\nEscaneá o ingresá el codigo de barras (solo numeros).",
                            action_executed="crear_producto",
                            success=True,
                            data={"product_data": pd, "awaiting": "barcode"}
                        )

            save_pending_product("default", pd)
            return _avanzar_creacion_producto(db, pd)

        # --- Detectar escaneo de codigo de barras ---
        bc_raw = user_message.strip()
        if re.match(r"^\d{6,}$", bc_raw):
            prod = db.query(Product).filter(Product.barcode == bc_raw).first()
            if prod:
                attrs = db.query(Attribute).join(ProductAttribute).filter(
                    ProductAttribute.product_id == prod.id
                ).all()
                attr_lines = []
                for a in attrs:
                    cat_name = db.query(Category.name).filter(Category.id == a.category_id).scalar()
                    attr_lines.append(f"  - {cat_name}: {a.name}")
                attr_str = "\n" + "\n".join(attr_lines) if attr_lines else ""
                return AgentResponse(
                    message=f"**Producto encontrado:**\nNombre: {prod.name}\nPrecio: ${prod.price}\nCodigo: {prod.barcode}{attr_str}",
                    action_executed="escanear_barcode",
                    success=True,
                    data={"id": prod.id, "name": prod.name, "price": prod.price, "barcode": prod.barcode}
                )
            save_pending_product("default", {"barcode": bc_raw, "nombre": None, "precio": None, "descripcion": None, "atributos_inferidos": []})
            return AgentResponse(
                message=f"No encontre ningun producto con el codigo **{bc_raw}**. ¿Que nombre le queres poner?",
                action_executed="escanear_barcode",
                success=False,
                data={"barcode": bc_raw, "awaiting_name": True}
            )

        # --- Flujo normal: clasificar intent ---
        intent_result = detect_intent(user_message)
        intent = intent_result.get("intent") if type(intent_result) == dict else intent_result

        print(f"[AGENT] Intent: {intent}")

        # --- Asignacion manual de producto a atributo (deterministico) ---
        # "asigna el producto X al atributo Y". No depende del clasificador ni
        # de ningun modelo: el usuario dice explicitamente producto y atributo.
        asign = _parse_asignar_producto_atributo(user_message)
        if asign and _is_valid_str(asign.get("producto")) and _is_valid_str(asign.get("target")):
            prod_nombre = asign["producto"]
            target_nombre = asign["target"]
            prods = db.query(Product).filter(Product.name.ilike(f"%{prod_nombre}%")).all()
            if not prods:
                return AgentResponse(
                    message=f"No encontre ningun producto que se llame '{prod_nombre}'. ¿Como se llama exactamente?",
                    action_executed="asignar_atributo",
                    success=False
                )
            # Resolver el target: puede ser un ATRIBUTO o una CATEGORIA. Ante
            # cualquier ambiguedad PREGUNTAMOS, no especulamos (regla del usuario).
            av = db.query(Attribute).filter(Attribute.name.ilike(f"%{target_nombre}%")).first()
            if not av:
                cat = db.query(Category).filter(Category.name.ilike(f"%{target_nombre}%")).first()
                if cat:
                    attrs_cat = db.query(Attribute).filter(Attribute.category_id == cat.id).all()
                    if len(attrs_cat) == 1:
                        av = attrs_cat[0]
                    elif len(attrs_cat) == 0:
                        return AgentResponse(
                            message=f"'{cat.name}' es una categoria y todavia no tiene atributos. ¿Que atributo de '{cat.name}' queres asignarle al producto '{prod_nombre}'?",
                            action_executed="asignar_atributo",
                            success=False,
                            data={"context": {"accion": "asignar_atributo", "producto": prod_nombre, "categoria": cat.name}}
                        )
                    else:
                        lista = ", ".join(a.name for a in attrs_cat)
                        return AgentResponse(
                            message=f"'{cat.name}' es una categoria con varios atributos ({lista}). ¿A cual queres asignar el producto '{prod_nombre}'?",
                            action_executed="asignar_atributo",
                            success=False,
                            data={"context": {"accion": "asignar_atributo", "producto": prod_nombre, "categoria": cat.name}}
                        )
                else:
                    # No existe ni atributo ni categoria: preguntar, NO inventar.
                    return AgentResponse(
                        message=f"No encontre un atributo ni una categoria llamada '{target_nombre}'. ¿Queres que cree el atributo '{target_nombre}' y se lo asigne al producto '{prod_nombre}'?",
                        action_executed="asignar_atributo",
                        success=False,
                        data={"context": {"accion": "crear_y_asignar_atributo", "producto": prod_nombre, "atributo": target_nombre}}
                    )
            asignados = 0
            for p in prods:
                existe = db.query(ProductAttribute).filter_by(product_id=p.id, attribute_id=av.id).first()
                if not existe:
                    db.add(ProductAttribute(product_id=p.id, attribute_id=av.id))
                    asignados += 1
            if asignados:
                db.commit()
            nombres = ", ".join(p.name for p in prods)
            if asignados:
                msg = f"Se asigno el atributo '{av.name}' al producto '{nombres}'."
            else:
                msg = f"El producto '{nombres}' ya tenia el atributo '{av.name}'."
            return AgentResponse(
                message=msg,
                action_executed="asignar_atributo",
                success=True,
                data={"attribute_id": av.id, "attribute": av.name, "productos_asignados": asignados, "productos": nombres}
            )

        # --- Override deterministico del intent de precios ---
        # El clasificador (Ollama 0.5b) es poco fiable: a veces manda un ajuste
        # claro a consulta_general. Si el mensaje trae un verbo imperativo de
        # ajuste de precios, forzamos ajustar_precios sin depender del modelo.
        PRECIO_CMD = {
            'aumentame', 'aumenta', 'aumentá', 'aumentales', 'aumentale',
            'subime', 'subi', 'subí', 'sube', 'subile', 'subiles',
            'incrementame', 'incrementa', 'incrementá',
            'bajame', 'baja', 'bajá', 'bajale', 'bajales',
            'disminuime', 'disminui', 'disminuí', 'disminuye',
            'reducime', 'reduci', 'reducí', 'reduce',
            'descontame', 'desconta', 'descontá', 'descuentame',
            'rebajame', 'rebaja', 'rebajá', 'sacale', 'sacales'
        }
        PRECIO_INF = {'aumentar', 'subir', 'incrementar', 'bajar', 'disminuir', 'reducir', 'descontar', 'rebajar'}
        _palabras_msg = set(re.findall(r'\w+', user_message.lower()))
        _tiene_pct = bool(re.search(r'\d+\s*%|\d+\s*por\s*ciento', user_message, re.IGNORECASE))
        if intent not in ("ajustar_precios", "aumentar_precios", "crear_productos", "crear_categoria", "agregar_atributo"):
            if _palabras_msg & PRECIO_CMD:
                intent = "ajustar_precios"
            elif (_palabras_msg & PRECIO_INF) and _tiene_pct:
                intent = "ajustar_precios"
            if intent == "ajustar_precios":
                print("[AGENT] Override deterministico -> ajustar_precios")

        if intent in ("ajustar_precios", "aumentar_precios"):
            print("ENTRO EN AJUSTAR_PRECIOS")

            price_type_result = detect_price_increase_type(user_message)
            tipo = price_type_result.get("tipo")
            porcentaje = price_type_result.get("porcentaje")
            operacion = str(price_type_result.get("operacion") or "aumento").strip().lower()
            attribute = price_type_result.get("attribute") or price_type_result.get("value")

            print("RESULTADO DEL DETECT_PRICE_INCREASE_TYPE", price_type_result)

            # --- Garantia deterministica del porcentaje ---
            # IncreaseDetector (0.5b) a veces no devuelve el porcentaje aunque
            # este explicito en el mensaje ("... un 30%"). Lo extraemos por regex.
            if not porcentaje:
                m_pct = re.search(r'(\d+(?:[.,]\d+)?)\s*%', user_message)
                if not m_pct:
                    m_pct = re.search(r'(\d+(?:[.,]\d+)?)\s*por\s*ciento', user_message, re.IGNORECASE)
                if m_pct:
                    porcentaje = float(m_pct.group(1).replace(",", "."))

            # --- Operacion derivada del verbo (mas fiable que el modelo 0.5b) ---
            if re.search(r'\b(baj\w*|disminu\w*|reduc\w*|descont\w*|rebaj\w*|sacale\w*|descuent\w*)\b', user_message, re.IGNORECASE):
                operacion = "disminucion"
            elif re.search(r'\b(aument\w*|subi\w*|sube\w*|increment\w*)\b', user_message, re.IGNORECASE):
                operacion = "aumento"

            # Operacion: aumento (+) o disminucion (-). El factor se calcula
            # despues de validar el porcentaje. verbo -> texto de la respuesta.
            signo = -1 if operacion == "disminucion" else 1
            verbo = "disminuyo" if signo < 0 else "aumento"

            stopwords = {'un','una','el','la','los','las','de','del','que','y','a','para','por','con','en','al','todo','todos',
                         'mi','tu','su','mis','tus','sus','proveedor','proveedores','marca','categoria','categoría',
                         'producto','productos','articulos','artículos','items','ítems',
                         'aumentame','subime','incrementa','incrementame','aumenta','sube','dame','poneme','pone','dejame',
                         'bajame','baja','disminuime','disminuye','reducime','reduci','reduce','descontame','descuento',
                         'rebajame','rebaja','sacale','hacele'}

            if attribute and ' ' in attribute.strip():
                parts = attribute.strip().split()
                attribute = parts[-1]
                if tipo == "individual":
                    tipo = "por_atributo"

            attr_extracted = None
            from_productos_pattern = False

            m = re.search(r'productos\s+de\s+\w+\s+(\w+)', user_message, re.IGNORECASE)
            if not m:
                m = re.search(r'productos\s+de\s+(\w+)', user_message, re.IGNORECASE)
            if not m:
                m = re.search(r'productos?\s+(\w+)', user_message, re.IGNORECASE)
            if m and m.group(1).lower() not in stopwords:
                attr_extracted = m.group(1)
                from_productos_pattern = True

            if not attr_extracted:
                m = re.search(r'(\w+)\s+un\s+\d+%', user_message)
                if m and m.group(1).lower() not in stopwords:
                    attr_extracted = m.group(1)
            if not attr_extracted:
                m = re.search(r'(?:aumentame|subime|incrementa|incrementame|bajame|disminuime|reducime|descontame|rebajame|sacale|hacele)\s+(?:los|las|un|el|la)?\s*(\w+)', user_message, re.IGNORECASE)
                if m and m.group(1).lower() not in stopwords:
                    attr_extracted = m.group(1)

            if attr_extracted:
                print(f"ATRIBUTO EXTRAIDO MANUALMENTE: {attr_extracted}")
                if not attribute:
                    attribute = attr_extracted
                if tipo == "todos" or (tipo == "individual" and from_productos_pattern):
                    tipo = "por_atributo"

            # Si el modelo no devolvio tipo pero tenemos un objetivo (atributo o
            # producto), asumimos por_atributo (prueba atributo y luego nombre/desc).
            if not tipo and attribute:
                tipo = "por_atributo"

            if not tipo:
                return AgentResponse(
                    message="No entendi bien el ajuste. ¿Que productos y que porcentaje queres aplicar?",
                    action_executed="ajustar_precios",
                    success=False
                )

            if not porcentaje:
                return AgentResponse(
                    message=f"Ingrese el porcentaje de {'disminucion' if signo < 0 else 'aumento'}.",
                    action_executed="ajustar_precios",
                    success=False
                )

            # Factor de ajuste: aumento (1 + %/100) o disminucion (1 - %/100)
            factor = 1 + signo * (porcentaje / 100)

            # --- Caso especial: ajuste por proveedor ---
            # "aumentame los productos de mi proveedor X", "bajale un 10% al proveedor X"
            if re.search(r'proveedor', user_message, re.IGNORECASE):
                m_prov = re.search(
                    r'proveedor(?:es)?\s+(?:de\s+|del\s+|la\s+|el\s+)?(.+?)(?:\s+(?:un|en|de|los|las)?\s*\d+\s*%?|\s*$)',
                    user_message, re.IGNORECASE
                )
                prov_val = m_prov.group(1).strip() if m_prov else ""
                if prov_val and prov_val.lower() not in stopwords:
                    prods_prov = db.query(Product).filter(Product.proveedor.ilike(f"%{prov_val}%")).all()
                    if not prods_prov:
                        # Fallback: atributo de categoria "proveedor" con ese valor
                        cat_prov = db.query(Category).filter(Category.name.ilike("proveedor")).first()
                        if cat_prov:
                            attr_prov = db.query(Attribute).filter(
                                Attribute.category_id == cat_prov.id,
                                Attribute.name.ilike(f"%{prov_val}%")
                            ).first()
                            if attr_prov:
                                pa_prov = db.query(ProductAttribute).filter(
                                    ProductAttribute.attribute_id == attr_prov.id
                                ).all()
                                pids_prov = [pa.product_id for pa in pa_prov]
                                if pids_prov:
                                    prods_prov = db.query(Product).filter(Product.id.in_(pids_prov)).all()
                    if prods_prov:
                        for p in prods_prov:
                            p.price = round(p.price * factor, 2)
                        db.commit()
                        return AgentResponse(
                            message=f"Se {verbo} un {porcentaje}% a {len(prods_prov)} producto(s) del proveedor '{prov_val}'",
                            action_executed="ajustar_precios",
                            success=True,
                            data={"updated_products": len(prods_prov), "proveedor": prov_val, "percentage": porcentaje, "operacion": operacion}
                        )
                    return AgentResponse(
                        message=f"No encontre productos del proveedor '{prov_val}'.",
                        action_executed="ajustar_precios",
                        success=False
                    )

            if tipo == "todos":
                print("ENTRANDO EN AUMENTAR A TODOS")
                products = db.query(Product).all()
                for p in products:
                    p.price = round(p.price * factor, 2)
                db.commit()
                return AgentResponse(
                    message=f"Se {verbo} el precio de TODOS los productos ({len(products)}) un {porcentaje}%",
                    action_executed="ajustar_precios",
                    success=True,
                    data={"updated_products": len(products), "percentage": porcentaje}
                )

            if tipo == "individual":
                print("ENTRANDO EN AUMENTAR INDIVIDUAL")
                if not attribute:
                    return AgentResponse(
                        message="No entendi que producto queres ajustar. ¿Podes decirme el nombre exacto?",
                        action_executed="ajustar_precios",
                        success=False
                    )
                products = db.query(Product).filter(Product.name.ilike(f"%{attribute}%")).all()
                if not products:
                    return AgentResponse(
                        message=f"No encontre ningun producto que se llame '{attribute}'.",
                        action_executed="ajustar_precios",
                        success=False
                    )
                for p in products:
                    p.price = round(p.price * factor, 2)
                db.commit()
                names = ", ".join([p.name for p in products])
                return AgentResponse(
                    message=f"Se {verbo} el precio de '{names}' ({len(products)} producto(s)) un {porcentaje}%",
                    action_executed="ajustar_precios",
                    success=True,
                    data={"updated_products": len(products), "percentage": porcentaje, "products": names}
                )

            elif tipo == "por_atributo":
                print("ENTRANDO A AUMENTAR POR ATRIBUTO", tipo)
                # Primero buscar el atributo directamente en la DB por nombre
                attr_record = AttributeService(db).get_by_name(attribute)

                if attr_record:
                    categoria_inf = db.query(Category.name).filter(Category.id == attr_record.category_id).scalar()
                    valor = attr_record.name
                    categoria_existe = True
                    cat = None
                else:
                    cats = db.query(Category).all()
                    existing_categories = [{"id": c.id, "name": c.name} for c in cats]

                    category_and_value = detect_category_and_value(attribute, existing_categories)
                    categoria_inf = category_and_value.get("categoria_inferida")
                    valor = category_and_value.get("valor")
                    categoria_existe = category_and_value.get("categoria_existe", False)

                    if not _is_valid_str(categoria_inf) or not _is_valid_str(valor):
                        categoria_inf = None

                    if not categoria_inf:
                        cat_fb = db.query(Category).filter(Category.name.ilike(f"%{attribute}%")).first()
                        if cat_fb:
                            attrs_fb = db.query(Attribute).filter(Attribute.category_id == cat_fb.id).all()
                            if attrs_fb:
                                attr_ids_fb = [a.id for a in attrs_fb]
                                pas_fb = db.query(ProductAttribute).filter(
                                    ProductAttribute.attribute_id.in_(attr_ids_fb)
                                ).all()
                                pids_fb = list(set(pa.product_id for pa in pas_fb))
                                if pids_fb:
                                    prods_fb = db.query(Product).filter(Product.id.in_(pids_fb)).all()
                                    for p in prods_fb:
                                        p.price = round(p.price * factor, 2)
                                    db.commit()
                                    return AgentResponse(
                                        message=f"Se {verbo} un {porcentaje}% a {len(prods_fb)} producto(s) de la categoria '{cat_fb.name}'",
                                        action_executed="ajustar_precios",
                                        success=True,
                                        data={"updated_products": len(prods_fb), "category": cat_fb.name, "percentage": porcentaje}
                                    )
                        return AgentResponse(
                            message=f"No pude determinar a que categoria pertenece '{attribute}'.",
                            action_executed="ajustar_precios",
                            success=False
                        )

                    cat = db.query(Category).filter(Category.name == categoria_inf).first()
                    if not cat:
                        try:
                            cat = Category(name=categoria_inf)
                            db.add(cat)
                            db.commit()
                            db.refresh(cat)
                        except Exception:
                            db.rollback()
                            cat = db.query(Category).filter(Category.name == categoria_inf).first()
                            if not cat:
                                return AgentResponse(
                                    message=f"Error al crear la categoria '{categoria_inf}'.",
                                    action_executed="ajustar_precios",
                                    success=False
                                )

                    attr_record = db.query(Attribute).filter(
                        Attribute.category_id == cat.id,
                        Attribute.name == valor
                    ).first()
                    if not attr_record:
                        attr_record = Attribute(category_id=cat.id, name=valor)
                        db.add(attr_record)
                        db.commit()
                        db.refresh(attr_record)

                product_attributes = db.query(ProductAttribute).filter(
                    ProductAttribute.attribute_id == attr_record.id
                ).all()
                product_ids = [b.product_id for b in product_attributes]

                if product_ids:
                    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
                    for p in products:
                        p.price = round(p.price * factor, 2)
                    db.commit()
                    return AgentResponse(
                        message=f"Se {verbo} un {porcentaje}% a {len(products)} producto(s) con {categoria_inf} = {valor}",
                        action_executed="ajustar_precios",
                        success=True,
                        data={"updated_products": len(products), "category": categoria_inf, "attribute": valor, "percentage": porcentaje}
                    )
                else:
                    matched = db.query(Product).filter(
                        (Product.name.ilike(f"%{valor}%")) | (Product.description.ilike(f"%{valor}%"))
                    ).all()
                    if matched:
                        for p in matched:
                            exists = db.query(ProductAttribute).filter_by(product_id=p.id, attribute_id=attr_record.id).first()
                            if not exists:
                                db.add(ProductAttribute(product_id=p.id, attribute_id=attr_record.id))
                            p.price = round(p.price * factor, 2)
                        db.commit()
                        return AgentResponse(
                            message=f"Se asigno '{valor}' y se {verbo} un {porcentaje}% a {len(matched)} producto(s).",
                            action_executed="ajustar_precios",
                            success=True,
                            data={"updated_products": len(matched), "category": categoria_inf, "attribute": valor, "percentage": porcentaje}
                        )
                    return AgentResponse(
                        message=f"No encontre productos con '{valor}' en nombre, descripcion ni atributos.",
                        action_executed="ajustar_precios",
                        success=False,
                        data={"context": {"intent": "ajustar_precios", "categoria": categoria_inf, "valor": valor, "porcentaje": porcentaje, "operacion": operacion}}
                    )

            elif tipo == "por_categoria":
                print("ENTRANDO EN AUMENTAR POR CATEGORIA")
                if not attribute:
                    return AgentResponse(
                        message="¿Que categoria queres ajustar?",
                        action_executed="ajustar_precios",
                        success=False
                    )
                cat = db.query(Category).filter(Category.name.ilike(f"%{attribute}%")).first()
                if not cat:
                    cats_list = ", ".join(c.name for c in db.query(Category).all())
                    return AgentResponse(
                        message=f"No encontre la categoria '{attribute}'. Categorias disponibles: {cats_list}",
                        action_executed="ajustar_precios",
                        success=False
                    )
                attrs = db.query(Attribute).filter(Attribute.category_id == cat.id).all()
                if not attrs:
                    return AgentResponse(
                        message=f"La categoria '{cat.name}' no tiene atributos asignados aun.",
                        action_executed="ajustar_precios",
                        success=False
                    )
                attr_ids = [a.id for a in attrs]
                pas = db.query(ProductAttribute).filter(
                    ProductAttribute.attribute_id.in_(attr_ids)
                ).all()
                pids = list(set(pa.product_id for pa in pas))
                if not pids:
                    return AgentResponse(
                        message=f"No hay productos con atributos de la categoria '{cat.name}'.",
                        action_executed="ajustar_precios",
                        success=False
                    )
                prods = db.query(Product).filter(Product.id.in_(pids)).all()
                for p in prods:
                    p.price = round(p.price * factor, 2)
                db.commit()
                return AgentResponse(
                    message=f"Se {verbo} un {porcentaje}% a {len(prods)} producto(s) de la categoria '{cat.name}'",
                    action_executed="ajustar_precios",
                    success=True,
                    data={"updated_products": len(prods), "category": cat.name, "percentage": porcentaje}
                )

            return AgentResponse(
                message="No pude procesar el ajuste. Asegurate de incluir el porcentaje.",
                action_executed="ajustar_precios",
                success=False
            )

        elif intent == "crear_productos":
            cats = db.query(Category).all()
            existing_categories = [{"id": c.id, "name": c.name} for c in cats]

            product_data = create_product_with_attributes(user_message, existing_categories)

            # Overrides deterministicos: lo que el usuario escribio literal manda
            # sobre lo que devuelve el modelo 0.5b (que a veces alucina).
            det = _parse_producto_deterministico(user_message)
            for campo in ("nombre", "precio", "barcode", "proveedor"):
                if det.get(campo) is not None and det.get(campo) != "":
                    product_data[campo] = det[campo]

            # Descripcion explicita en el mensaje inicial ("... descripcion X")
            m_desc = re.search(r'(?:descripcion|descripción|desc)\s*:?\s+(.+)$', user_message, re.IGNORECASE)
            desc_explicita = bool(m_desc and m_desc.group(1).strip())
            if desc_explicita:
                product_data["descripcion"] = m_desc.group(1).strip()

            # Solo damos por resuelto (no volver a preguntar) lo que el usuario dio
            # EXPLICITO. Lo que venga del modelo se preguntara igual (no especular).
            if _is_valid_str(det.get("proveedor")):
                product_data["_prov_ok"] = True
            if desc_explicita:
                product_data["_desc_ok"] = True

            # El flujo pide lo que falte (nombre -> precio -> descripcion ->
            # proveedor -> barcode) y crea el producto cuando esta completo.
            return _avanzar_creacion_producto(db, product_data)

        elif intent == "crear_categoria":
            m = re.search(r'(?:categoria|categoría)\s+["""]?(.+?)["""]?\s*$', user_message, re.IGNORECASE)
            if m and m.group(1).strip():
                cat_name = _limpiar_nombre_categoria(m.group(1))
                if not cat_name:
                    return AgentResponse(
                        message="No entendi el nombre de la categoria. Decime por ejemplo: 'creame la categoria marca'.",
                        action_executed="crear_categoria",
                        success=False
                    )
                existing = db.query(Category).filter(Category.name == cat_name).first()
                if existing:
                    return AgentResponse(
                        message=f"La categoria '{cat_name}' ya existe.",
                        action_executed="crear_categoria",
                        success=False
                    )
                cat = Category(name=cat_name)
                db.add(cat)
                db.commit()
                return AgentResponse(
                    message=f"Categoria '{cat_name}' creada exitosamente!",
                    action_executed="crear_categoria",
                    success=True,
                    data={"id": cat.id, "name": cat.name}
                )
            # Fallback: "agrupar por X", "clasificar por X", "por X"
            m_por = re.search(r'(?:agrupar|agrupa|agrupá|clasificar|clasifica|separar|ordenar)?\s*por\s+(.+)$', user_message, re.IGNORECASE)
            cat_name = _limpiar_nombre_categoria(m_por.group(1)) if m_por else ""
            if cat_name:
                existing = db.query(Category).filter(Category.name == cat_name).first()
                if existing:
                    return AgentResponse(
                        message=f"La categoria '{cat_name}' ya existe.",
                        action_executed="crear_categoria",
                        success=False
                    )
                cat = Category(name=cat_name)
                db.add(cat)
                db.commit()
                return AgentResponse(
                    message=f"Categoria '{cat_name}' creada exitosamente!",
                    action_executed="crear_categoria",
                    success=True,
                    data={"id": cat.id, "name": cat.name}
                )
            return AgentResponse(
                message="No entendi el nombre de la categoria. Decime por ejemplo: 'creame la categoria marca'.",
                action_executed="crear_categoria",
                success=False
            )

        elif intent == "listar_categorias":
            cats = db.query(Category).all()
            if cats:
                lines = ["**Categorias y atributos disponibles:**\n"]
                for c in cats:
                    attributes = db.query(Attribute).filter(Attribute.category_id == c.id).all()
                    attrs_str = ", ".join([a.name for a in attributes]) if attributes else "sin atributos"
                    lines.append(f"  - {c.name}: {attrs_str}")
                return AgentResponse(
                    message="\n".join(lines),
                    action_executed="listar_categorias",
                    success=True,
                    data={"categories": [{"id": c.id, "name": c.name} for c in cats]}
                )
            return AgentResponse(
                message="No hay categorias configuradas. ¿Queres crear alguna?",
                action_executed="listar_categorias",
                success=True
            )

        elif intent == "agregar_atributo":
            cats = db.query(Category).all()
            existing_categories = [{"id": c.id, "name": c.name} for c in cats]
            attr = None
            # El VALOR del atributo lo dice el usuario explicitamente. NO usamos
            # ningun modelo para inferirlo: el 0.5b alucina (devolvia "Pepperoni"
            # o "material" para cosas que no dijo el usuario). Si no se puede
            # extraer del texto, PREGUNTAMOS en vez de especular.
            if not attr or not _is_valid_str(attr.get("categoria")) or not _is_valid_str(attr.get("valor")):
                idx = re.search(r'(?:atributo|attributo)\s+', user_message, re.IGNORECASE)
                if idx:
                    rest = user_message[idx.end():]
                    val = re.split(r'\s+(?:y\s+|asignal\w*|asigna\w*|para\s+)', rest, maxsplit=1, flags=re.IGNORECASE)[0].strip().rstrip('.,;:¿?"""''')
                    cat_name = None
                    if val:
                        m2 = re.search(r'^["""]?(.+?)["""]?\s+(?:de|en)\s+["""]?(.+?)["""]?$', val, re.IGNORECASE)
                        if m2:
                            posible_val = m2.group(1).strip()
                            posible_cat = re.sub(r'^(?:la\s+|el\s+)?(?:categoria|categoría)\s+', '', m2.group(2).strip(), flags=re.IGNORECASE).strip()
                            _cats_low = [c["name"].lower() for c in existing_categories]
                            # Aceptar "... de/en X" como categoria SOLO si es explicito
                            # ("... categoria X") o X ya existe como categoria.
                            # Asi "galletas de chocolate" queda como un unico valor.
                            if re.search(r'(?:categoria|categoría)', m2.group(2), re.IGNORECASE) or posible_cat.lower() in _cats_low:
                                val = posible_val
                                cat_name = posible_cat
                        cat_name = cat_name or detect_category_and_value(val, existing_categories).get("categoria_inferida")
                        if val:
                            attr = {"categoria": cat_name if _is_valid_str(cat_name) else "tipo", "valor": val}

            if not attr:
                return AgentResponse(
                    message="No entendi que atributo y categoria queres agregar. Decime por ejemplo: 'agregar atributo ropa de categoria indumentaria'",
                    action_executed="agregar_atributo",
                    success=False
                )
            cat_name = attr.get("categoria")
            val = attr.get("valor")

            categoria_existe = bool(db.query(Category).filter(Category.name == cat_name).first())
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

            # --- Auto-asignar a productos que coincidan ---
            productos = db.query(Product).all()
            productos_list = [{"id": p.id, "name": p.name, "description": p.description or ""} for p in productos]
            resolved = resolve_attribute_in_db(cat_name, val, categoria_existe, productos_list)
            productos_ids = resolved.get("productos_detectados", [])
            asignados = 0
            for pid in productos_ids:
                existe = db.query(ProductAttribute).filter_by(product_id=pid, attribute_id=av.id).first()
                if not existe:
                    db.add(ProductAttribute(product_id=pid, attribute_id=av.id))
                    asignados += 1
            if asignados:
                db.commit()

            msg = f"Atributo '{val}' agregado a categoria '{cat_name}'."
            if asignados:
                msg += f" Se asigno automaticamente a {asignados} producto(s)."
            else:
                msg += " No se encontraron productos para asignar automaticamente."

            return AgentResponse(
                message=msg,
                action_executed="agregar_atributo",
                success=True,
                data={"attribute_id": av.id, "category": cat_name, "value": val, "productos_asignados": asignados}
            )

        elif intent == "info_incompleta":
            ctx = context or intent_result
            result = handle_incomplete_info(user_message, ctx)
            return AgentResponse(
                message=result.get("pregunta", "No entendi bien. ¿Podes darme mas detalles?"),
                action_executed="info_incompleta",
                success=True,
                data={"missing_field": result.get("campo_faltante"), "context": ctx}
            )

        else:
            # --- Fallback: accion ambigua o incompleta ---
            # El mensaje cayo en consulta_general, pero si contiene un verbo de
            # accion de gestion probablemente el usuario intenta HACER algo y le
            # falto informacion. En ese caso pedimos una aclaracion puntual con
            # IncompleteHandler en vez de una respuesta generica del asesor.
            # Los faltantes de flujos concretos (porcentaje, nombre, precio,
            # barcode) NO llegan aca: se resuelven inline mas arriba.
            VERBOS_ACCION = (
                'aumentar', 'aumentame', 'aumenta', 'aumentá', 'subir', 'subime', 'subi', 'subí', 'sube',
                'incrementar', 'incrementame', 'incrementa',
                'bajar', 'bajame', 'baja', 'bajá', 'disminuir', 'disminuime', 'disminui', 'disminuí',
                'reducir', 'reducime', 'reduci', 'reducí', 'reduce', 'descontar', 'descontame',
                'rebajar', 'rebajame', 'rebaja',
                'crear', 'crea', 'creá', 'creame', 'crealo', 'crearme',
                'agregar', 'agrega', 'agregá', 'agregame', 'agregale', 'agregalo', 'añadir', 'añade', 'sumar',
                'poner', 'pone', 'poné', 'poneme', 'ponele',
                'cambiar', 'cambia', 'cambiá', 'modificar', 'modifica', 'modificá',
                'asignar', 'asigna', 'asigná', 'asignale',
                'borrar', 'borra', 'borrá', 'borrame', 'eliminar', 'elimina', 'eliminá',
                'sacar', 'saca', 'sacá', 'sacale'
            )
            palabras = re.findall(r'\w+', user_message.lower())
            tiene_porcentaje = bool(re.search(r'\d+\s*%|\d+\s*por\s*ciento', user_message, re.IGNORECASE))
            # Si el mensaje trae un porcentaje explicito no es "incompleto":
            # es una accion concreta que el clasificador no supo rutear.
            es_accion_incompleta = any(v in palabras for v in VERBOS_ACCION) and not tiene_porcentaje

            if es_accion_incompleta:
                ctx = context or {"intent_detectado": intent, "mensaje_original": user_message}
                result = handle_incomplete_info(user_message, ctx)
                return AgentResponse(
                    message=result.get("pregunta", "No entendi bien que queres hacer. ¿Podes darme mas detalles?"),
                    action_executed="info_incompleta",
                    success=True,
                    data={"missing_field": result.get("campo_faltante"), "context": ctx}
                )

            total_products = db.query(Product).count()
            bridge_count = db.query(ProductAttribute).count()
            avg_price = db.query(Product).with_entities(sqlfunc.avg(Product.price)).scalar()
            min_price = db.query(Product).with_entities(sqlfunc.min(Product.price)).scalar()
            max_price = db.query(Product).with_entities(sqlfunc.max(Product.price)).scalar()

            cats = db.query(Category).all()
            cat_stats = {}
            for c in cats:
                attr_count = db.query(Attribute).filter(Attribute.category_id == c.id).count()
                cat_stats[c.name] = attr_count

            db_stats = {
                "total_productos": total_products,
                "productos_sin_atributos": total_products - bridge_count if total_products > 0 else 0,
                "precio_promedio": round(avg_price, 2) if avg_price else 0,
                "precio_minimo": min_price if min_price else 0,
                "precio_maximo": max_price if max_price else 0,
                "categorias_y_valores": cat_stats
            }

            response = handle_general_query(user_message, db_stats)
            return AgentResponse(
                message=response,
                action_executed="consulta_general",
                success=True,
                data={"stats": db_stats}
            )

    except Exception as e:
        print(f"[ERROR] Agent: {e}")
        import traceback
        traceback.print_exc()
        return AgentResponse(
            message=f"Ocurrio un error: {str(e)}",
            action_executed=None,
            success=False,
            data={"error": str(e)}
        )
