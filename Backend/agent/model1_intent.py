
import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_intent

def detect_intent(message: str, conversation_history: list = None, llm=None) -> dict:
    
    llm = get_intent() 
    
    if conversation_history is None:
        conversation_history = []
    
    template = """{user_message}
JSON:"""
    
    prompt = PromptTemplate(
        input_variables=["user_message"],
        template=template
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "user_message": message
        })
        
        content = response.strip()
        # Limpiar markdown y códigos si están presentes
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        return data
    except Exception as e:
        print(f"Error detecting intent: {e}")
        return {"intent": "consulta_general", "confidence": 0.5, "error": str(e)}