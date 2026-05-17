from .ollama_client import call_ollama_json


def build_system_prompt(target: str, existing_categories: list) -> str:
    cats_str = ", ".join([c["name"] if isinstance(c, dict) else c for c in existing_categories]) if existing_categories else "No hay categorias disponibles"
    return f"""Eres un clasificador de atributos de productos.
El usuario quiere aumentar precios de productos que tienen una caracteristica especifica.
Las categorias de atributos disponibles en el sistema son:

{cats_str}

Dado el texto "{target}", devuelve UNICAMENTE un JSON con este formato, sin texto adicional:

{{
  "categoria_inferida": "<nombre de categoria existente o nombre sugerido si no existe>",
  "valor": "<valor del atributo>",
  "categoria_existe": <true o false>
}}

Ejemplos:
- target "plastico", categorias existentes ["material", "marca"] -> {{"categoria_inferida": "material", "valor": "plastico", "categoria_existe": true}}
- target "Adidas", categorias existentes ["material", "marca"] -> {{"categoria_inferida": "marca", "valor": "Adidas", "categoria_existe": true}}
- target "rojo", categorias existentes ["material", "marca"] -> {{"categoria_inferida": "color", "valor": "rojo", "categoria_existe": false}}

Responde SOLO con el JSON."""


def detect_category_and_value(target: str, existing_categories: list) -> dict:
    system_prompt = build_system_prompt(target, existing_categories)
    result = call_ollama_json(system_prompt, f"Clasifica el target '{target}'")
    if not result or "categoria_inferida" not in result:
        return {"categoria_inferida": None, "valor": target, "categoria_existe": False}
    return result
