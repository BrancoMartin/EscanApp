from .ollama_client import call_ollama_json
from Modelfiles import CreateProduct
import json


def create_product(user_prompt: str, existing_categories: list) -> dict:
    
    llm = CreateProduct

    if not existing_categories: 
        existing_categories = []

    template = "MENSAJE: {user_prompt}, {existing_categories}"

    prompt = PromptTemplate(
        input_variables=[user_prompt, existing_categories]
        template = template,
    )

    chain = prompt | llm

    try: 
        response = chain.invoke({
            "user_message": prompt,
        })

        content = response.strip()
        # Limpiar markdown y códigos si están presentes
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        return data
    except Exception as e: 
        print(f"Error detecting intent: {e}")
        return {"intent": "consulta_general", "confidence": 0.5, "error": str(e)}

