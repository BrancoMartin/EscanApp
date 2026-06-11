import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import create_categories_by_products

_NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})

def create_categories(nombre, descripcion, proveedor):
    llm = create_categories_by_products()

    template = """
nombre: {nombre}
descripcion: {descripcion}
proveedor: {proveedor}

Crea categorias de atributo de ESTE producto específico.
"""

    prompt = PromptTemplate(
        input_variables=["nombre", "descripcion", "proveedor"],
        template=template
    )

    chain = prompt | llm

    try:
        response = chain.invoke({
            "nombre": nombre,
            "descripcion": descripcion,
            "proveedor": proveedor
        })

        content = response.strip()
        clean = content.replace("```json", "").replace("```", "").strip()
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
        print(f"[create_categories] Error: {e}")
        return {"categorias_nuevas": []}