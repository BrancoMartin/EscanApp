import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_attribute_resolver


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

    llm = get_attribute_resolver()

    template = "Buscar: categoria=\"{categoria}\", valor=\"{valor}\"\nProductos:\n{productos}\nJSON:"

    prompt = PromptTemplate(
        input_variables=["categoria", "valor", "productos"],
        template=template,
    )

    chain = prompt | llm

    try:
        response = chain.invoke({
            "categoria": categoria,
            "valor": valor,
            "productos": prod_str
        })

        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)

        if not data or "puede_inferir" not in data:
            return {"puede_inferir": False, "productos_detectados": [], "mensaje_usuario": "No se pudo determinar. Por favor indicanos que productos tienen este atributo."}
        return data
    except Exception as e:
        print(f"Error resolving attribute: {e}")
        return {"puede_inferir": False, "productos_detectados": [], "mensaje_usuario": "No se pudo determinar. Por favor indicanos que productos tienen este atributo."}
