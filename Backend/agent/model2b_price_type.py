from .ollama_client import call_ollama_json


def detect_price_increase_type(user_prompt: str) -> dict:
    result = call_ollama_json("DetectorAumento", user_prompt)
    if not result or "tipo" not in result:
        return {"tipo": None, "porcentaje": None, "target": None}
    return result
