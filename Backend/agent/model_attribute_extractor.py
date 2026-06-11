import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_attribute_extractor


_NULL_SYNONYMS = frozenset({
    'null', 'none', 'nada', 'vacio', 'vacío', 'ninguno', 'ninguna',
    'nil', 'empty', 'blank', 'unknown', 'desconocido', 'na', 'n/a', '-'
})


def attribute_extractor(nombre, descripcion, categoria, proveedor):
    llm = get_attribute_extractor()

    template = """nombre: {nombre}
descripcion: {descripcion}
proveedor: {proveedor}
categorias_existentes: {categoria}"""

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

        if isinstance(data, list):
            data = [
                a for a in data
                if isinstance(a, dict)
                and isinstance(a.get("valor"), str)
                and a["valor"].strip().lower() not in _NULL_SYNONYMS
            ]
        return data
    except Exception as e:
        print(f"[attribute_extractor] Error: {e}")
        return []