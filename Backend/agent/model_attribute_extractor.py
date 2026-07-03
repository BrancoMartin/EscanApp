import json
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_attribute_extractor


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


def attribute_extractor(nombre, descripcion, categoria, proveedor):
    print("ENTRANDO AL MODEL_ATTRIBUT_EXTRACTOR AL CREAR UN PRODUCTO")
    llm = get_attribute_extractor()
    template = "nombre: {nombre}\ndescripcion: {descripcion}\nproveedor: {proveedor}\ncategorias_existentes: {categoria}"
    prompt = PromptTemplate(input_variables=["nombre", "descripcion", "proveedor", "categoria"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"nombre": nombre, "descripcion": descripcion, "proveedor": proveedor, "categoria": categoria})
        print("RESPUESTA CRUDA DEL MODELO DE ATRIBUTOS: ", response)
        
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        print("ATRIBUTOS: ", data)

        for d in data: 
            atributte = d.get("valor", "").strip().lower()
            print("ATRIBUTO", atributte)
            if atributte not in SINONIMOS_NULL and atributte != "":
                d["valor"] = atributte

        proveedor_valido = str(proveedor or "").strip().lower()
        categorias_existentes = [str(cat).strip().lower() for cat in (categoria or [])]
        tiene_proveedor = any(str(attr.get("categoria", "")).strip().lower() == "proveedor" for attr in data)

        if (
            proveedor_valido not in SINONIMOS_NULL
            and proveedor_valido != ""
            and "proveedor" in categorias_existentes
            and not tiene_proveedor
        ):
            data.append({"categoria": "proveedor", "valor": proveedor_valido})

        return data
    except Exception as e:
        print(f"[attr_extract] Error: {e}")
        return []
