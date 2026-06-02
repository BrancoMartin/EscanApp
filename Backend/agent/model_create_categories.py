import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import create_categories_by_products

def create_categories(nombre,descripcion,proveedor, categoria):
    llm = create_categories_by_products()

    template = f"""
        nombre: {nombre}
        descripcion: {descripcion}
        proveedor: {proveedor}

            Crea categorias de ESTE producto específico.
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

    except Exception as e: 
        print(f"[create_categories] Error: {e}")
        return {"categories": []}