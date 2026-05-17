from .ollama_client import call_ollama


def build_system_prompt(user_prompt: str, db_stats: dict) -> str:
    stats_str = "\n".join([f"- {k}: {v}" for k, v in db_stats.items()]) if db_stats else "Sin estadisticas disponibles"
    return f"""Eres un asesor inteligente de una app de gestion de productos con codigo de barras para pequenos comercios.
Tenes acceso a las siguientes estadisticas actuales del negocio:

{stats_str}

El usuario te hace la siguiente consulta: "{user_prompt}"

Respondé de forma clara, concisa y util. Podes dar recomendaciones basadas en los datos.
Si los datos no son suficientes para responder, indicá que informacion adicional se necesitarian.
Responde en texto libre (no en JSON), de forma conversacional."""


def handle_general_query(user_prompt: str, db_stats: dict) -> str:
    system_prompt = build_system_prompt(user_prompt, db_stats)
    result = call_ollama(system_prompt, user_prompt)
    if result is None:
        return "No pude procesar la consulta. Asegurate de que Ollama este funcionando."
    return result
