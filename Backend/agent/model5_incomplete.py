from .ollama_client import call_ollama_json


def build_system_prompt(user_prompt: str, context: dict) -> str:
    context_str = "\n".join([f"{k}: {v}" for k, v in context.items()]) if context else "Sin contexto previo"
    return f"""Eres un asistente amigable de una app de gestion de productos.
El usuario quiso realizar una accion pero su mensaje esta incompleto o es ambiguo.

Contexto de lo que se pudo detectar hasta ahora:
{context_str}

Mensaje original del usuario: "{user_prompt}"

Tu tarea es formular UNA SOLA pregunta corta y clara para obtener la informacion que falta.
No hagas multiples preguntas a la vez. Se directo y amigable.

Devuelve UNICAMENTE un JSON con este formato, sin texto adicional:

{{
  "pregunta": "<pregunta para el usuario>",
  "campo_faltante": "<nombre del campo que se necesita: porcentaje, producto, atributo, categoria, etc>"
}}

Responde SOLO con el JSON."""


def handle_incomplete_info(user_prompt: str, context: dict) -> dict:
    system_prompt = build_system_prompt(user_prompt, context)
    result = call_ollama_json(system_prompt, user_prompt)
    if not result or "pregunta" not in result:
        return {"pregunta": "No entendi bien. ¿Podes darme mas detalles?", "campo_faltante": "general"}
    return result
