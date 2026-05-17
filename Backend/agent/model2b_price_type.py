from .ollama_client import call_ollama_json

SYSTEM_PROMPT = """Eres un analizador de instrucciones de actualizacion de precios.
Dado el mensaje del usuario, devuelve UNICAMENTE un JSON con este formato, sin texto adicional:

{
  "tipo": "<tipo de aumento>",
  "porcentaje": <numero>,
  "target": "<descripcion del target o null>"
}

Los tipos posibles son:
- "todos": el usuario quiere aumentar todos los productos
- "individual": el usuario menciona un producto especifico por nombre
- "por_atributo": el usuario menciona una caracteristica como material, marca, color, tamano, etc.

Ejemplos:
- "aumentame todos los productos un 15%" -> {"tipo": "todos", "porcentaje": 15, "target": null}
- "aumentame la leche un 30%" -> {"tipo": "individual", "porcentaje": 30, "target": "leche"}
- "aumentame los productos de plastico un 20%" -> {"tipo": "por_atributo", "porcentaje": 20, "target": "plastico"}
- "aumentame los de marca Adidas un 12%" -> {"tipo": "por_atributo", "porcentaje": 12, "target": "Adidas"}

Responde SOLO con el JSON, sin explicaciones."""


def detect_price_increase_type(user_prompt: str) -> dict:
    result = call_ollama_json(SYSTEM_PROMPT, user_prompt)
    if not result or "tipo" not in result:
        return {"tipo": None, "porcentaje": None, "target": None}
    return result
