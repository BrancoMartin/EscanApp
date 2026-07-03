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


def create_categories(nombre, descripcion, proveedor, categorias_existentes=None):
    print("ENTRANDO AL MODEL_CREATE_CATEGORIES")
    print("PROVEEDOR: ", proveedor)
    llm = create_categories_by_products()
    template = "\nnombre: {nombre}\ndescripcion: {descripcion}\nproveedor: {proveedor}\ncategorias_existentes: {categorias_existentes}\n\nCrea categorias de atributo de ESTE producto especifico."
    prompt = PromptTemplate(input_variables=["nombre", "descripcion", "proveedor", "categorias_existentes"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"nombre": nombre, "descripcion": descripcion, "proveedor": proveedor, "categorias_existentes": categorias_existentes or []})
        print(f"[DEBUG] Respuesta cruda del modelo: {response}")
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        cats = data.get("categorias_nuevas", [])
        categorias_validas = []
        print("Categorias: ", cats)
        for categoria in cats:
            print("CATEGORIA: ", categoria)
            nombre_categoria = str(categoria).strip().lower()
            if nombre_categoria not in SINONIMOS_NULL and nombre_categoria != "" and nombre_categoria not in categorias_validas:
                categorias_validas.append(nombre_categoria)

        proveedor_valido = str(proveedor or "").strip().lower()
        categorias_actuales = [str(categoria).strip().lower() for categoria in (categorias_existentes or [])]

        if (
            proveedor_valido not in SINONIMOS_NULL
            and proveedor_valido != ""
            and "proveedor" not in categorias_actuales
            and "proveedor" not in categorias_validas
        ):
            categorias_validas.append("proveedor")

        data["categorias_nuevas"] = categorias_validas

        print("data['categorias_nuevas']: ", data["categorias_nuevas"])
        return data
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[create_cats] Error: {e}")
        return {"categorias_nuevas": []}
