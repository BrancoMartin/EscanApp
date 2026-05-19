from .ollama_client import call_ollama_json


def detect_category_and_value(target: str, existing_categories: list) -> dict:
    cats_str = ", ".join([c["name"] if isinstance(c, dict) else c for c in existing_categories]) if existing_categories else "No hay categorias disponibles"
    message = f"Target: {target}\nCategorias existentes: {cats_str}"
    result = call_ollama_json("ClasificadorAtributo", message)

    print("RESULTADO DEL CLASIFICADOR DE CATEGORIAS", result)

    if not result or "categoria_inferida" not in result:
        return {"categoria_inferida": None, "valor": target, "categoria_existe": False}
    return result
