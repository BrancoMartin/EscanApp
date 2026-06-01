
import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_value_extractor


def value_extractor(nombre,descripcion,proveedor, categoria):
    llm = get_value_extractor()

    template = """
                Tipo de respuesta: {{"atributos": [{{"categoria": "proveedor", "valor": "Deportes SA"}}, {{"categoria": "marca", "valor": "Nike"}}, {{"categoria": "material", "valor": "cuero"}}]}}
                "{nombre}", "{descripcion}", "{proveedor}, Categorias Existentes: {categoria}"
            """

    prompt = PromptTemplate(
        input_variables = ["nombre", "descripcion", "proveedor", "categoria"],
        template=template
    )

    chain = prompt | llm

    try: 
        response = chain.invoke({
            "nombre":nombre,
            "descripcion": descripcion,
            "proveedor": proveedor,
            "categoria": categoria
        })

        content = response.strip()
        # Limpiar markdown y códigos si están presentes
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        return data
    except Exception as e:
        print(f"[value_extractor] Error: {e}")
        return {"atributos": []}
