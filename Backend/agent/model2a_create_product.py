from .ollama_client import call_ollama_json
from ollama_client import get_create_product
from langchain_core.prompts import PromptTemplate
import json


def create_product(user_prompt: str, existing_categories: list) -> dict:
    
    llm = get_create_product()

    if not existing_categories: 
        existing_categories = []

    template = "MENSAJE: {user_prompt}, {existing_categories}"

    prompt = PromptTemplate(
        input_variables=["user_prompt", "existing_categories"]
        template = template,
    )

    chain = prompt | llm

    try: 
        # aca ejecutamos la chain y le pasamos los valores los input variables
        response = chain.invoke({
            "user_prompt": user_prompt,
            "existing_categories": existing_categories
        })

        content = response.strip()
        # Limpiar markdown y códigos si están presentes
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        return data
    except Exception as e: 
        print(f"Error detecting intent: {e}")
        return {"intent": "consulta_general", "confidence": 0.5, "error": str(e)}

