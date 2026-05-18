from .ollama_client import call_ollama_json

def detect_intent(user_prompt: str) -> dict:
    result = call_ollama_json("CualifiquerIntent", user_prompt)
    if not result or "intent" not in result:
        return {"intent": "info_incompleta", "confidence": 0.5, "raw_data": user_prompt}
    return result
