from .ollama_client import call_ollama_json


def build_system_prompt(existing_categories: list) -> str:
    cats_str = ", ".join([c["name"] if isinstance(c, dict) else c for c in existing_categories]) if existing_categories else "No hay categorias disponibles"
    return f"""Eres un asistente de carga de productos para una app de gestion con codigo de barras.
El usuario quiere registrar un nuevo producto. Tenes las siguientes categorias de atributos disponibles en el sistema:

{cats_str}

Dado el mensaje del usuario, devuelve UNICAMENTE un JSON con este formato, sin texto adicional:

{{
  "nombre": "<nombre del producto>",
  "precio": <numero o null si no se menciona>,
  "descripcion": "<descripcion o null>",
  "proveedor": "<proveedor o null>",
  "atributos_inferidos": [
    {{"categoria": "<nombre de categoria>", "valor": "<valor inferido>"}}
  ]
}}

Infiere los atributos SOLO si podes determinarlo con certeza desde el nombre o descripcion del producto.
Ejemplo: "Pelota Adidas cuero" -> atributos: [{{"categoria": "marca", "valor": "Adidas"}}, {{"categoria": "material", "valor": "cuero"}}]
Si no podes inferir un atributo con certeza, no lo incluyas.
Responde SOLO con el JSON."""


def create_product_with_attributes(user_prompt: str, existing_categories: list) -> dict:
    system_prompt = build_system_prompt(existing_categories)
    result = call_ollama_json(system_prompt, user_prompt)
    if not result or "nombre" not in result:
        return {"nombre": None, "precio": None, "descripcion": None, "proveedor": None, "atributos_inferidos": []}
    return result
