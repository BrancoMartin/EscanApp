from .ollama_client import call_ollama_json

SYSTEM_PROMPT = """Eres un clasificador de intenciones para una app de gestion de productos con codigo de barras.
Dado el mensaje del usuario, devuelve UNICAMENTE un JSON con el siguiente formato, sin texto adicional:

{
  "intent": "<intencion>",
  "confidence": <numero entre 0 y 1>,
  "raw_data": "<texto relevante extraido del prompt>"
}

Las intenciones posibles son:
- "crear_producto": el usuario quiere registrar un producto nuevo
- "aumentar_precio": el usuario quiere aumentar el precio de uno o mas productos
- "crear_categoria": el usuario quiere crear una categoria de atributo nueva
- "agregar_valor": el usuario quiere agregar un valor a una categoria existente
- "listar_categorias": el usuario quiere ver las categorias o atributos disponibles
- "info_incompleta": el mensaje no tiene suficiente informacion para ejecutar ninguna accion
- "consulta_general": el usuario hace una pregunta general, pide estadisticas o recomendaciones

Si no estas seguro, usa "info_incompleta".
Responde SOLO con el JSON, sin explicaciones."""


def detect_intent(user_prompt: str) -> dict:
    result = call_ollama_json(SYSTEM_PROMPT, user_prompt)
    if not result or "intent" not in result:
        return {"intent": "info_incompleta", "confidence": 0.5, "raw_data": user_prompt}
    return result
