from .ollama_client import call_ollama_json


def handle_incomplete_info(user_prompt: str, context: dict) -> dict:
    context_str = "\n".join([f"{k}: {v}" for k, v in context.items()]) if context else "Sin contexto previo"
    message = f"Contexto de lo que se pudo detectar hasta ahora:\n{context_str}\n\nMensaje original del usuario: \"{user_prompt}\""
    result = call_ollama_json("ManejadorIncompleto", message)
    if not result or "pregunta" not in result:
        return {"pregunta": "No entendi bien. ¿Podes darme mas detalles?", "campo_faltante": "general"}
    return result
