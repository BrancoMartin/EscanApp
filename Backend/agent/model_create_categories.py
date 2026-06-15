import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import create_categories_by_products

_NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})


def create_categories(nombre, descripcion, proveedor):
    llm = create_categories_by_products()
    template = "\nnombre: {nombre}\ndescripcion: {descripcion}\nproveedor: {proveedor}\n\nCrea categorias de atributo de ESTE producto especifico."
    prompt = PromptTemplate(input_variables=["nombre", "descripcion", "proveedor"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"nombre": nombre, "descripcion": descripcion, "proveedor": proveedor})
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        cats = data.get("categorias_nuevas", [])
        if isinstance(cats, list):
            data["categorias_nuevas"] = [
                c for c in cats
                if isinstance(c, dict)
                and isinstance(c.get("nombre"), str)
                and c["nombre"].strip().lower() not in _NULL_SYNONYMS
            ]
        return data
    except Exception as e:
        print(f"[create_cats] Error: {e}")
        return {"categorias_nuevas": []}
