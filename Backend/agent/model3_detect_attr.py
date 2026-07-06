import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_attribute_classifier

_NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})


def detect_category_and_value(value: str, existing_categories: list) -> dict:
    cats_str = ", ".join(c["name"] if type(c) == dict else c for c in existing_categories) if existing_categories else ""
    if not cats_str:
        return {"categoria_inferida": value, "valor": value, "categoria_existe": False}

    llm = get_attribute_classifier()
    template = "Valor: {value}\nCategorias: {categories}\nJSON:"
    prompt = PromptTemplate(input_variables=["value", "categories"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"value": value, "categories": cats_str})
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        if not data or "categoria_inferida" not in data:
            return {"categoria_inferida": None, "valor": value, "categoria_existe": False}
        cat_inf = data.get("categoria_inferida")
        val = data.get("valor")
        if type(cat_inf) != str or cat_inf.strip().lower() in _NULL_SYNONYMS:
            data["categoria_inferida"] = None
        if type(val) != str or val.strip().lower() in _NULL_SYNONYMS:
            data["valor"] = value
        return data
    except Exception as e:
        print(f"[classify_attr] Error: {e}")
        return {"categoria_inferida": None, "valor": value, "categoria_existe": False}
