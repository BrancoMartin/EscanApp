import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_intent


def detect_intent(message: str) -> dict:
    llm = get_intent()
    template = "{user_message}\nJSON:"
    prompt = PromptTemplate(input_variables=["user_message"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"user_message": message})
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        print(f"[intent] Error: {e}")
        return {"intent": "consulta_general", "confidence": 0.5}
