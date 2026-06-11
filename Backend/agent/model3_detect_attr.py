import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_attribute_classifier

_NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})


def detect_category_and_value(value: str, existing_categories: list) -> dict:
    cats_str = ", ".join([c["name"] if isinstance(c, dict) else c for c in existing_categories]) if existing_categories else "No hay categorias disponibles"

    llm = get_attribute_classifier()

    template = """Clasifica el siguiente valor de atributo en una categoria existente.
Devuelve SOLO un JSON sin texto adicional:

{{
  "categoria_inferida": "nombre de la categoria mas adecuada de la lista",
  "valor": "{value}",
  "categoria_existe": true o false segun si la categoria inferida esta en la lista de categorias proporcionadas
}}

Atributo: {value}
Categorias disponibles: {categories}
JSON:"""

    prompt = PromptTemplate(
        input_variables=["value", "categories"],
        template=template,
    )

    chain = prompt | llm

    try:
        response = chain.invoke({
            "value": value,
            "categories": cats_str
        })

        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)

        print("RESULTADO DEL CLASIFICADOR DE CATEGORIAS", data)

        if not data or "categoria_inferida" not in data:
            return {"categoria_inferida": None, "valor": value, "categoria_existe": False}

        cat_inf = data.get("categoria_inferida")
        val = data.get("valor")
        if not isinstance(cat_inf, str) or cat_inf.strip().lower() in _NULL_SYNONYMS:
            data["categoria_inferida"] = None
        if not isinstance(val, str) or val.strip().lower() in _NULL_SYNONYMS:
            data["valor"] = value
        return data
    except Exception as e:
        print(f"Error classifying attribute: {e}")
        return {"categoria_inferida": None, "valor": value, "categoria_existe": False}
