import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_incomplete_handler


def handle_incomplete_info(user_prompt: str, context: dict) -> dict:
    context_str = "\n".join([f"{k}: {v}" for k, v in context.items()]) if context else "Sin contexto previo"

    llm = get_incomplete_handler()

    template = "Contexto de lo que se pudo detectar hasta ahora:\n{context}\n\nMensaje original del usuario: \"{message}\""

    prompt = PromptTemplate(
        input_variables=["context", "message"],
        template=template,
    )

    chain = prompt | llm

    try:
        response = chain.invoke({
            "context": context_str,
            "message": user_prompt
        })

        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)

        if not data or "pregunta" not in data:
            return {"pregunta": "No entendi bien. ¿Podes darme mas detalles?", "campo_faltante": "general"}
        return data
    except Exception as e:
        print(f"Error handling incomplete info: {e}")
        return {"pregunta": "No entendi bien. ¿Podes darme mas detalles?", "campo_faltante": "general"}
