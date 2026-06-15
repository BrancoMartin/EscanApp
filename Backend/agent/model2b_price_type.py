import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_increase_detector


def detect_price_increase_type(user_prompt: str) -> dict:
    llm = get_increase_detector()
    template = "{user_prompt}\nJSON:"
    prompt = PromptTemplate(input_variables=["user_prompt"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"user_prompt": user_prompt})
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        print(f"[price_type] Error: {e}")
        return {"tipo": "todos", "porcentaje": None}
