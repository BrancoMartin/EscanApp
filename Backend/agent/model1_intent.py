from .ollama_client import call_ollama_json
import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_intent

def detect_intent(message: str, conversation_history: list = None, llm=None) -> dict:
    
    llm = get_intent() 
    
    if conversation_history is None:
        conversation_history = []
    
    # Construir contexto del historial
    context = "\n".join([
        f"Usuario: {msg.get('user', '')}\nAsistente: {msg.get('assistant', '')}"
        for msg in conversation_history[-4:]  # Últimos 4 mensajes para contexto
    ])
    
    template = """MENSAJE: "{user_message}"

INTENCIONES: crear_categoria, agregar_atributo, aumentar_precios, crear_productos, consulta_general

JSON:"""
    
    prompt = PromptTemplate(
        input_variables=["user_message", "context"],
        template=template
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "user_message": message,
            "context": context if context else "Conversación nueva"
        })
        
        content = response.strip()
        # Limpiar markdown y códigos si están presentes
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        return data
    except Exception as e:
        print(f"Error detecting intent: {e}")
        return {"intent": "consulta_general", "confidence": 0.5, "error": str(e)}