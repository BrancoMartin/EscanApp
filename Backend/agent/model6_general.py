from langchain_core.prompts import PromptTemplate
from .ollama_client import get_general_consultant


def handle_general_query(user_prompt: str, db_stats: dict) -> str:
    stats_str = "\n".join([f"- {k}: {v}" for k, v in db_stats.items()]) if db_stats else "Sin estadisticas disponibles"

    llm = get_general_consultant()

    template = "Estadisticas actuales del negocio:\n{stats}\n\nConsulta del usuario: \"{message}\""

    prompt = PromptTemplate(
        input_variables=["stats", "message"],
        template=template,
    )

    chain = prompt | llm

    try:
        response = chain.invoke({
            "stats": stats_str,
            "message": user_prompt
        })
        return response.strip()
    except Exception as e:
        print(f"Error handling general query: {e}")
        return "No pude procesar la consulta. Asegurate de que Ollama este funcionando."
