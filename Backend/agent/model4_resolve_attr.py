from .ollama_client import call_ollama_json


def resolve_attribute_in_db(categoria: str, valor: str, categoria_existe: bool, productos: list) -> dict:
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

    message = f"Atributo buscado: categoria \"{categoria}\", valor \"{valor}\"\n\nLista de productos disponibles:\n{prod_str}"
    result = call_ollama_json("ResolvedorAtributo", message)
    if not result or "puede_inferir" not in result:
        return {"puede_inferir": False, "productos_detectados": [], "mensaje_usuario": "No se pudo determinar. Por favor indicanos que productos tienen este atributo."}
    return result
