
import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_attribute_extractor


def attribute_extractor(nombre, descripcion, categoria, proveedor):
    llm = get_attribute_extractor()

    template = """
nombre: {nombre}
descripcion: {descripcion}
proveedor: {proveedor}
categorias_existentes: {categoria}

Extraé los atributos de ESTE producto específico.

REGLAS:
- Usá SOLO las categorías de "categorias_existentes", no inventes otras
- Si "proveedor" está vacío, NO incluyas {"categoria": "proveedor", ...}
- No incluyas atributos con valor vacío
- Extraé los valores reales del nombre y la descripción

FORMATO:
[{"categoria": "...", "valor": "..."}]
"""

    prompt = PromptTemplate(
        input_variables=["nombre", "descripcion", "proveedor", "categoria"],
        template=template
    )

    chain = prompt | llm

    try:
        response = chain.invoke({
            "nombre": nombre,
            "descripcion": descripcion,
            "proveedor": proveedor,
            "categoria": categoria
        })

        content = response.strip()
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return data
    except Exception as e:
        print(f"[attribute_extractor] Error: {e}")
        return []
