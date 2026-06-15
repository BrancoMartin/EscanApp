from .ollama_client import get_create_product
from langchain_core.prompts import PromptTemplate
import json

_NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})


def create_product_with_attributes(user_prompt: str, existing_categories: list) -> dict:
    llm = get_create_product()
    cats = existing_categories or []
    template = "MENSAJE: {user_prompt}, {existing_categories}"
    prompt = PromptTemplate(input_variables=["user_prompt", "existing_categories"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"user_prompt": user_prompt, "existing_categories": cats})
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        atributos = data.get("atributos_inferidos", [])
        if isinstance(atributos, list):
            data["atributos_inferidos"] = [
                a for a in atributos
                if isinstance(a, dict)
                and isinstance(a.get("categoria"), str) and a["categoria"].strip().lower() not in _NULL_SYNONYMS
                and isinstance(a.get("valor"), str) and a["valor"].strip().lower() not in _NULL_SYNONYMS
            ]
        return data
    except Exception as e:
        print(f"[create_product] Error: {e}")
        return {"nombre": None, "precio": None, "atributos_inferidos": []}
