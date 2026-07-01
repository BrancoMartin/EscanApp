import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import create_categories_by_products

SINONIMOS_NULL = [
    "null",
    "none",
    "nada",
    "vacio",
    "vacío",
    "ninguno",
    "ninguna",
    "nil",
    "empty",
    "blank",
    "unknown",
    "desconocido",
    "na",
    "n/a",
    "-"
]


def create_categories(nombre, descripcion, proveedor):
    print("ENTRANDO AL MODEL_CREATE_CATEGORIES")
    llm = create_categories_by_products()
    template = "\nnombre: {nombre}\ndescripcion: {descripcion}\nproveedor: {proveedor}\n\nCrea categorias de atributo de ESTE producto especifico."
    prompt = PromptTemplate(input_variables=["nombre", "descripcion", "proveedor"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"nombre": nombre, "descripcion": descripcion, "proveedor": proveedor})
        print(f"[DEBUG] Respuesta cruda del modelo: {response}")
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        cats = data.get("categorias_nuevas", [])
        categorias_validas = []
        for categoria in data.get("categorias_nuevas", []):
            nombre = categoria.get("nombre", "").strip().lower()

            if nombre not in SINONIMOS_NULL and nombre != "":
                categorias_validas.append(categoria)

        data["categorias_nuevas"] = categorias_validas
        return data
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[create_cats] Error: {e}")
        return {"categorias_nuevas": []}
