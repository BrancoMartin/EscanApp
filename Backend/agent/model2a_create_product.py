from .ollama_client import call_ollama_json


def create_product_with_attributes(user_prompt: str, existing_categories: list) -> dict:
    cats_str = ", ".join([c["name"] if isinstance(c, dict) else c for c in existing_categories]) if existing_categories else "No hay categorias disponibles"
    message = f"Categorias disponibles: {cats_str}\n\nMensaje del usuario: {user_prompt}"
    result = call_ollama_json("CreadorProductos", message)
    if not result or "nombre" not in result:
        return {"nombre": None, "precio": None, "descripcion": None, "proveedor": None, "atributos_inferidos": []}
    return result
