import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_attribute_resolver


def resolve_attribute_in_db(categoria: str, valor: str, categoria_existe: bool, productos: list) -> dict:
    if not productos:
        prod_str = "Sin productos"
    else:
        lines = [f"ID: {p.get('id','')} | Nombre: {p.get('name','')} | Desc: {p.get('description','')}" for p in productos]
        prod_str = "\n".join(lines)

    llm = get_attribute_resolver()
    template = "Categoria=\"{categoria}\" Valor=\"{valor}\"\nProductos:\n{productos}\nJSON:"
    prompt = PromptTemplate(input_variables=["categoria", "valor", "productos"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"categoria": categoria, "valor": valor, "productos": prod_str})
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        if not data or "puede_inferir" not in data:
            return {"puede_inferir": False, "productos_detectados": []}
        return data
    except Exception as e:
        print(f"[resolve_attr] Error: {e}")
        return {"puede_inferir": False, "productos_detectados": []}
