from .ollama_client import get_create_product
from langchain_core.prompts import PromptTemplate
import json

SINONIMOS_NULL = [
    "null",
    "none",
    "nada",
    "vacio",
    "vacío",
    "ninguno",
    "ninguna",
    "nil",
    "empty",
    "blank",
    "unknown",
    "desconocido",
    "na",
    "n/a",
    "-"
]


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

        # El Modelfile CreateProduct devuelve la clave "atributos"; el resto del
        # sistema espera "atributos_inferidos". Aceptamos ambas y normalizamos.
        atributos = data.get("atributos_inferidos")
        if atributos is None:
            atributos = data.get("atributos", [])

        atributos_validos = []
        if type(atributos) == list:
            for a in atributos:
                if type(a) != dict:
                    continue
                categoria = a.get("categoria")
                valor = a.get("valor")
                if type(categoria) != str or type(valor) != str:
                    continue
                nombre_categoria = categoria.strip().lower()
                nombre_valor = valor.strip().lower()
                if nombre_categoria in SINONIMOS_NULL or nombre_categoria == "":
                    continue
                if nombre_valor in SINONIMOS_NULL or nombre_valor == "":
                    continue
                atributos_validos.append(a)

        data["atributos_inferidos"] = atributos_validos
        return data
    except Exception as e:
        print(f"[create_product] Error: {e}")
        return {"nombre": None, "precio": None, "atributos_inferidos": []}
