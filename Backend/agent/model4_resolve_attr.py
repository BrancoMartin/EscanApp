from .ollama_client import call_ollama_json


def build_system_prompt(categoria: str, valor: str, productos: list) -> str:
    if not productos:
        prod_str = "No hay productos disponibles."
    else:
        lines = []
        for p in productos:
            p_id = p.get("id", p.get("ID", "?"))
            p_name = p.get("name", p.get("Name", p.get("nombre", "?")))
            p_desc = p.get("description", p.get("Description", p.get("descripcion", "")))
            lines.append(f"ID: {p_id} | Nombre: {p_name} | Descripcion: {p_desc}")
        prod_str = "\n".join(lines)

    return f"""Eres un asistente que determina que productos de una lista podrian tener un atributo especifico.
Atributo buscado: categoria "{categoria}", valor "{valor}".

Lista de productos disponibles (nombre y descripcion):
{prod_str}

Devuelve UNICAMENTE un JSON con este formato, sin texto adicional:

{{
  "puede_inferir": <true o false>,
  "productos_detectados": [<lista de product_ids que probablemente tengan este atributo>],
  "mensaje_usuario": "<mensaje para mostrar al usuario explicando lo que se detecto o lo que se necesita>"
}}

Si los nombres o descripciones de los productos contienen el valor buscado claramente, puede_inferir = true.
Si no hay informacion suficiente para determinarlo, puede_inferir = false y productos_detectados = [].
Responde SOLO con el JSON."""


def resolve_attribute_in_db(categoria: str, valor: str, categoria_existe: bool, productos: list) -> dict:
    system_prompt = build_system_prompt(categoria, valor, productos)
    result = call_ollama_json(system_prompt, f"Determina que productos tienen el atributo {categoria}:{valor}")
    if not result or "puede_inferir" not in result:
        return {"puede_inferir": False, "productos_detectados": [], "mensaje_usuario": "No se pudo determinar. Por favor indicanos que productos tienen este atributo."}
    return result
