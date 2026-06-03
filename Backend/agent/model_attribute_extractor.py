
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
