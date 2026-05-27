from .ollama_client import call_ollama_json
import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_value_extractor


def value_extractor(nombre,descripcion,proveedor):
    llm = get_value_extractor()


    context = "\n".join([
        f"Usuario: {msg.get('user', '')}\nAsistente: {msg.get('assistant', '')}"
    ])

    template = """
                Tipo de respuesta: {"atributos": [{"categoria": "proveedor", "valor": "Deportes SA"}, {"categoria": "marca", "valor": "Nike"}, {"categoria": "material", "valor": "cuero"}]}
                "{nombre}", "{descripcion}", "{proveedor}"
            """

    prompt = PromptTemplate(
        input_variables = ["nombre", "descripcion", "proveedor"],
        template=template
    )

    chain = prompt | llm

    try: 
        response = chain.invoke({
            "nombre":nombre,
            "descripcion": descripcion,
            "proveedor": proveedor 
        })

        content = response.strip()
        # Limpiar markdown y códigos si están presentes
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        return data
    except Exception as e:
        print(f"Error detecting intent: {e}")
        return {"intent": "consulta_general", "confidence": 0.5, "error": str(e)}
