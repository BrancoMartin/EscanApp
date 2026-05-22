import json
from langchain.prompts import PromptTemplate
from .ollama_client import get_increase_detector


def detect_price_increase_type(user_prompt: str) -> dict:
    
    llm = get_increase_detector()

    template = """
    {user_prompt}
    opciones: "todos", "individual", "por_atributo"
    """
    
    prompt = PromptTemplate(
        input_variables=["user_prompt"],
        template=template,
    )
    
    chain = prompt | llm

    try:
        response = chain.invoke({
            "user_prompt": user_prompt
        })

        content = response.strip()
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        return data
    except Exception as e:
        print(f"Error detecting price increase type: {e}")
        return {"tipo": "todos", "porcentaje": None, "error": str(e)}