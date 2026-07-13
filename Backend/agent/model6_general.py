from langchain_core.prompts import PromptTemplate
from .ollama_client import get_general_consultant


def handle_general_query(user_prompt: str, db_stats: dict) -> str:
    stats_str = "\n".join(f"- {k}: {v}" for k, v in db_stats.items()) if db_stats else "Sin datos disponibles"
    llm = get_general_consultant()
    # "DATOS" y no "Estadisticas": el Modelfile instruye a responder solo con lo
    # que venga bajo DATOS, y a no inventar lo que no este ahi.
    template = "DATOS:\n{stats}\n\nUsuario: {message}"
    prompt = PromptTemplate(input_variables=["stats", "message"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"stats": stats_str, "message": user_prompt})
        return response.strip()
    except Exception as e:
        print(f"[general] Error: {e}")
        return "No pude procesar la consulta."
