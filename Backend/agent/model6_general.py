from .ollama_client import call_ollama


def handle_general_query(user_prompt: str, db_stats: dict) -> str:
    stats_str = "\n".join([f"- {k}: {v}" for k, v in db_stats.items()]) if db_stats else "Sin estadisticas disponibles"
    message = f"Estadisticas actuales del negocio:\n{stats_str}\n\nConsulta del usuario: \"{user_prompt}\""
    result = call_ollama("ConsultorGeneral", message)
    if result is None:
        return "No pude procesar la consulta. Asegurate de que Ollama este funcionando."
    return result
