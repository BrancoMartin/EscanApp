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
from Backend.services.attribute_service import AttributeService

load_dotenv()

router = APIRouter()


_NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})

def _is_valid_str(v):
    return isinstance(v, str) and v.strip().lower() not in _NULL_SYNONYMS


_pending_products: dict = {}

def save_pending_product(session_id: str, product_data: dict):
    _pending_products[session_id] = product_data

def get_pending_product(session_id: str) -> dict | None:
    return _pending_products.get(session_id)

def clear_pending_product(session_id: str):
    _pending_products.pop(session_id, None)


def _enriquecer_producto_con_atributos(db: Session, product: Product, user_message: str = ""):
    cats = db.query(Category).all()
    cats_str = ", ".join(c.name for c in cats) if cats else ""
    atributos_extra = attribute_extractor(product.name, product.description or "", cats_str, "")
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
            product_data = pending
            nombre = product_data.get("nombre")

            if not nombre:
                nombre = user_message.strip()
                if not nombre or re.match(r"^\d+$", nombre):
                    return AgentResponse(
                        message="¿Que nombre tiene el producto?",
                        action_executed="crear_producto",
                        success=False,
                        data={"product_data": product_data, "awaiting_name": True}
                    )
                product_data["nombre"] = nombre
                save_pending_product("default", product_data)
                return AgentResponse(
                    message=f"Producto: {nombre}\n\n¿Que precio tiene?",
                    action_executed="crear_producto",
                    success=True,
                    data={"product_data": product_data, "awaiting_price": True}
                )

            if not product_data.get("precio"):
                precio_match = re.search(r'(\d+[\.,]?\d*)', user_message)
                if not precio_match:
                    return AgentResponse(
                        message=f"Producto: {nombre}\n\nNo entendi el precio. ¿Podes decirme el valor numerico?",
                        action_executed="crear_producto",
                        success=False,
                        data={"product_data": product_data, "awaiting_price": True}
                    )
                product_data["precio"] = float(precio_match.group(1).replace(",", "."))
                save_pending_product("default", product_data)
                if not product_data.get("barcode"):
                    return AgentResponse(
                        message=f"Datos del producto:\nNombre: {nombre}\nPrecio: ${product_data['precio']}\n\nAhora escaneá o ingresá el codigo de barras.",
                        action_executed="crear_producto",
                        success=True,
                        data={"product_data": product_data}
                    )

            if not product_data.get("barcode"):
                barcode_raw = user_message.strip()
                if re.match(r"^\d+$", barcode_raw):
                    product_data["barcode"] = barcode_raw
                else:
                    bc_match = re.search(r'\b(\d{6,})\b', user_message)
                    if bc_match:
                        product_data["barcode"] = bc_match.group(1)
                    else:
                        return AgentResponse(
                            message=f"Datos del producto:\nNombre: {nombre}\nPrecio: ${product_data.get('precio')}\n\nEscaneá o ingresá el codigo de barras (solo numeros).",
                            action_executed="crear_producto",
                            success=True,
                            data={"product_data": product_data}
                        )
                save_pending_product("default", product_data)

            # Completar creacion: ya tenemos precio + barcode
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
                        bridge = ProductAttribute(product_id=product.id, attribute_id=av.id)
                        db.add(bridge)
                db.commit()

            extras = _enriquecer_producto_con_atributos(db, product)
            if extras:
                print(f"[ENRIQUECER] {extras} atributos adicionales asignados a '{nombre}'")

            clear_pending_product("default")
            return AgentResponse(
                message=f"Producto '{nombre}' creado exitosamente!",
                action_executed="crear_producto",
                success=True,
                data={"id": product.id, "name": product.name, "price": product.price, "barcode": product.barcode}
            )

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
        intent = intent_result.get("intent") if isinstance(intent_result, dict) else intent_result

        print(f"[AGENT] Intent: {intent}")

        if intent == "aumentar_precios":
            print("ENTRO EN AUMENTAR_PRECIOS")
            
            price_type_result = detect_price_increase_type(user_message)
            tipo = price_type_result.get("tipo")
            porcentaje = price_type_result.get("porcentaje")
            attribute = price_type_result.get("attribute") or price_type_result.get("value")

            print("RESULTADO DEL DETECT_PRICE_INCREASE_TYPE", price_type_result)

            stopwords = {'un','una','el','la','los','las','de','del','que','y','a','para','por','con','en','al','todo','todos',
                         'producto','productos','articulos','artículos','items','ítems',
                         'aumentame','subime','incrementa','dame','poneme','pone','dejame'}

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
                m = re.search(r'(?:aumentame|subime|incrementa)\s+(?:los|las)\s+(\w+)', user_message, re.IGNORECASE)
                if m and m.group(1).lower() not in stopwords:
                    attr_extracted = m.group(1)

            if attr_extracted:
                print(f"ATRIBUTO EXTRAIDO MANUALMENTE: {attr_extracted}")
                if not attribute:
                    attribute = attr_extracted
                if tipo == "todos" or (tipo == "individual" and from_productos_pattern):
                    tipo = "por_atributo"

            if not tipo:
                return AgentResponse(
                    message="No entendi bien el aumento. ¿Que productos y porcentaje queres aplicar?",
                    action_executed="aumentar_precios",
                    success=False
                )

            if not porcentaje:
                return AgentResponse(
                    message="Ingrese el porcentaje de aumento.",
                    action_executed="aumentar_precios",
                    success=False
                )

            if tipo == "todos":
                print("ENTRANDO EN AUMENTAR A TODOS")
                products = db.query(Product).all()
                for p in products:
                    p.price = round(p.price * (1 + porcentaje / 100), 2)
                db.commit()
                return AgentResponse(
                    message=f"Se aumento el precio de TODOS los productos ({len(products)}) un {porcentaje}%",
                    action_executed="aumentar_precios",
                    success=True,
                    data={"updated_products": len(products), "percentage": porcentaje}
                )

            if tipo == "individual":
                print("ENTRANDO EN AUMENTAR INDIVIDUAL")
                if not attribute:
                    return AgentResponse(
                        message="No entendi que producto queres aumentar. ¿Podes decirme el nombre exacto?",
                        action_executed="aumentar_precios",
                        success=False
                    )
                products = db.query(Product).filter(Product.name.ilike(f"%{attribute}%")).all()
                if not products:
                    return AgentResponse(
                        message=f"No encontre ningun producto que se llame '{attribute}'.",
                        action_executed="aumentar_precios",
                        success=False
                    )
                for p in products:
                    p.price = round(p.price * (1 + porcentaje / 100), 2)
                db.commit()
                names = ", ".join([p.name for p in products])
                return AgentResponse(
                    message=f"Se aumento el precio de '{names}' ({len(products)} producto(s)) un {porcentaje}%",
                    action_executed="aumentar_precios",
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
                                        p.price = round(p.price * (1 + porcentaje / 100), 2)
                                    db.commit()
                                    return AgentResponse(
                                        message=f"Se aumento un {porcentaje}% a {len(prods_fb)} producto(s) de la categoria '{cat_fb.name}'",
                                        action_executed="aumentar_precios",
                                        success=True,
                                        data={"updated_products": len(prods_fb), "category": cat_fb.name, "percentage": porcentaje}
                                    )
                        return AgentResponse(
                            message=f"No pude determinar a que categoria pertenece '{attribute}'.",
                            action_executed="aumentar_precios",
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
                                    action_executed="aumentar_precios",
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
                        p.price = round(p.price * (1 + porcentaje / 100), 2)
                    db.commit()
                    return AgentResponse(
                        message=f"Se aumento un {porcentaje}% a {len(products)} producto(s) con {categoria_inf} = {valor}",
                        action_executed="aumentar_precios",
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
                            p.price = round(p.price * (1 + porcentaje / 100), 2)
                        db.commit()
                        return AgentResponse(
                            message=f"Se asigno '{valor}' y se aumento un {porcentaje}% a {len(matched)} producto(s).",
                            action_executed="aumentar_precios",
                            success=True,
                            data={"updated_products": len(matched), "category": categoria_inf, "attribute": valor, "percentage": porcentaje}
                        )
                    return AgentResponse(
                        message=f"No encontre productos con '{valor}' en nombre, descripcion ni atributos.",
                        action_executed="aumentar_precios",
                        success=False,
                        data={"context": {"intent": "aumentar_precios", "categoria": categoria_inf, "valor": valor, "porcentaje": porcentaje}}
                    )

            elif tipo == "por_categoria":
                print("ENTRANDO EN AUMENTAR POR CATEGORIA")
                if not attribute:
                    return AgentResponse(
                        message="¿Que categoria queres aumentar?",
                        action_executed="aumentar_precios",
                        success=False
                    )
                cat = db.query(Category).filter(Category.name.ilike(f"%{attribute}%")).first()
                if not cat:
                    cats_list = ", ".join(c.name for c in db.query(Category).all())
                    return AgentResponse(
                        message=f"No encontre la categoria '{attribute}'. Categorias disponibles: {cats_list}",
                        action_executed="aumentar_precios",
                        success=False
                    )
                attrs = db.query(Attribute).filter(Attribute.category_id == cat.id).all()
                if not attrs:
                    return AgentResponse(
                        message=f"La categoria '{cat.name}' no tiene atributos asignados aun.",
                        action_executed="aumentar_precios",
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
                        action_executed="aumentar_precios",
                        success=False
                    )
                prods = db.query(Product).filter(Product.id.in_(pids)).all()
                for p in prods:
                    p.price = round(p.price * (1 + porcentaje / 100), 2)
                db.commit()
                return AgentResponse(
                    message=f"Se aumento un {porcentaje}% a {len(prods)} producto(s) de la categoria '{cat.name}'",
                    action_executed="aumentar_precios",
                    success=True,
                    data={"updated_products": len(prods), "category": cat.name, "percentage": porcentaje}
                )

            return AgentResponse(
                message="No pude procesar el aumento. Asegurate de incluir el porcentaje.",
                action_executed="aumentar_precios",
                success=False
            )

        elif intent == "crear_productos":
            cats = db.query(Category).all()
            existing_categories = [{"id": c.id, "name": c.name} for c in cats]

            product_data = create_product_with_attributes(user_message, existing_categories)
            nombre = product_data.get("nombre")
            precio = product_data.get("precio")

            if not nombre:
                return AgentResponse(
                    message="No entendi el nombre del producto. ¿Podes repetirlo?",
                    action_executed="crear_producto",
                    success=False
                )

            if not precio:
                save_pending_product("default", product_data)
                return AgentResponse(
                    message=f"Producto: {nombre}\n\n¿Que precio tiene?",
                    action_executed="crear_producto",
                    success=True,
                    data={"product_data": product_data, "awaiting_price": True}
                )

            if re.match(r"^\d+$", user_message.strip()):
                pending = get_pending_product("default")
                if pending:
                    product_data = pending
                    product_data["barcode"] = user_message.strip()

            if "barcode" not in product_data or not product_data.get("barcode"):
                save_pending_product("default", product_data)
                return AgentResponse(
                    message=f"Datos del producto:\nNombre: {nombre}\nPrecio: ${precio}\n\nAhora escaneá o ingresá el codigo de barras.",
                    action_executed="crear_producto",
                    success=True,
                    data={"product_data": product_data}
                )

            existing = db.query(Product).filter(Product.barcode == product_data["barcode"]).first()
            if existing:
                return AgentResponse(
                    message=f"Ya existe un producto con ese codigo de barras: {existing.name}",
                    action_executed="crear_producto",
                    success=False
                )

            product = Product(
                name=nombre,
                price=float(precio),
                barcode=product_data["barcode"],
                description=product_data.get("descripcion")
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
                        bridge = ProductAttribute(product_id=product.id, attribute_id=av.id)
                        db.add(bridge)
                db.commit()

            extras = _enriquecer_producto_con_atributos(db, product)
            if extras:
                print(f"[ENRIQUECER] {extras} atributos adicionales asignados a '{nombre}'")

            clear_pending_product("default")
            return AgentResponse(
                message=f"Producto '{nombre}' creado exitosamente!",
                action_executed="crear_producto",
                success=True,
                data={"id": product.id, "name": product.name, "price": product.price, "barcode": product.barcode}
            )

        elif intent == "crear_categoria":
            m = re.search(r'(?:categoria|categoría)\s+["""]?(.+?)["""]?\s*$', user_message, re.IGNORECASE)
            if m and m.group(1).strip():
                cat_name = m.group(1).strip().rstrip('.')
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
                message="No entendi el nombre de la categoria. ¿Podes repetirlo?",
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
            result = create_product_with_attributes(user_message, existing_categories)
            attr = None
            if result.get("atributos_inferidos"):
                attr = result["atributos_inferidos"][0]

            if not attr or not _is_valid_str(attr.get("categoria")) or not _is_valid_str(attr.get("valor")):
                idx = re.search(r'(?:atributo|attributo)\s+', user_message, re.IGNORECASE)
                if idx:
                    rest = user_message[idx.end():]
                    val = re.split(r'\s+(?:y\s+|asignal\w*|asigna\w*|para\s+)', rest, maxsplit=1, flags=re.IGNORECASE)[0].strip().rstrip('.,;:¿?"""''')
                    cat_name = None
                    if val:
                        m2 = re.search(r'^["""]?(.+?)["""]?\s+(?:de|en)\s+["""]?(.+?)["""]?$', val, re.IGNORECASE)
                        if m2:
                            val = m2.group(1).strip()
                            cat_name = m2.group(2).strip()
                        cat_name = cat_name or detect_category_and_value(val, existing_categories).get("categoria_inferida")
                        if val:
                            attr = {"categoria": cat_name if _is_valid_str(cat_name) else val, "valor": val}

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
