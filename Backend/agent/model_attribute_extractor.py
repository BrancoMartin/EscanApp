import json
import re
from langchain_core.prompts import PromptTemplate
from .ollama_client import get_attribute_extractor


# Tope de atributos que aceptamos del modelo. El 0.5b tiende a emitir un atributo
# por CADA categoria existente (inventando valores), lo que agota num_predict y
# trunca el JSON. Nos quedamos con los primeros: el resto es relleno alucinado.
MAX_ATRIBUTOS = 3

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


def _parsear_lista_atributos(texto: str) -> list:
    """Parsea la lista de atributos que devolvio el modelo.

    Si el modelo se corta por num_predict, el JSON queda truncado
    ("Unterminated string") y json.loads descarta TODA la respuesta. Eso no es
    gratis: quedarnos sin atributos dispara el fallback a CreateCategories, o
    sea un SEGUNDO modelo, y el request pasa de ~2s a ~19s. Por eso, si el JSON
    no parsea, rescatamos los objetos {"categoria","valor"} que si quedaron
    completos."""
    try:
        data = json.loads(texto)
        if type(data) == list:
            return data
        if type(data) == dict:
            return [data]
        return []
    except ValueError:
        pass

    rescatados = []
    patron = r'\{\s*"categoria"\s*:\s*"([^"]*)"\s*,\s*"valor"\s*:\s*"([^"]*)"\s*\}'
    for m in re.finditer(patron, texto):
        rescatados.append({"categoria": m.group(1), "valor": m.group(2)})
    if rescatados:
        print(f"[attr_extract] JSON truncado: se rescataron {len(rescatados)} atributos completos")
    return rescatados


def attribute_extractor(nombre, descripcion, categoria, proveedor):
    llm = get_attribute_extractor()
    template = "nombre: {nombre}\ndescripcion: {descripcion}\nproveedor: {proveedor}\ncategorias_existentes: {categoria}"
    prompt = PromptTemplate(input_variables=["nombre", "descripcion", "proveedor", "categoria"], template=template)
    chain = prompt | llm
    try:
        response = chain.invoke({"nombre": nombre, "descripcion": descripcion, "proveedor": proveedor, "categoria": categoria})

        clean = response.strip().replace("```json", "").replace("```", "").strip()
        data = _parsear_lista_atributos(clean)

        atributos_validos = []
        for d in data:
            if type(d) != dict:
                continue
            cat = d.get("categoria")
            val = d.get("valor")
            if type(cat) != str or type(val) != str:
                continue
            nombre_categoria = cat.strip().lower()
            nombre_valor = val.strip().lower()
            if nombre_categoria in SINONIMOS_NULL or nombre_categoria == "":
                continue
            if nombre_valor in SINONIMOS_NULL or nombre_valor == "":
                continue
            atributos_validos.append({"categoria": nombre_categoria, "valor": nombre_valor})

        atributos_validos = atributos_validos[:MAX_ATRIBUTOS]

        # Red de seguridad deterministica (SDD ai-agent): el proveedor lo escribio
        # el usuario, no hace falta que lo infiera un modelo. Si el modelo lo
        # omitio, lo agregamos nosotros.
        proveedor_valido = str(proveedor or "").strip().lower()
        categorias_existentes = [str(cat).strip().lower() for cat in (categoria or [])]

        tiene_proveedor = False
        for attr in atributos_validos:
            if attr.get("categoria") == "proveedor":
                tiene_proveedor = True

        if (
            proveedor_valido not in SINONIMOS_NULL
            and proveedor_valido != ""
            and "proveedor" in categorias_existentes
            and not tiene_proveedor
        ):
            atributos_validos.append({"categoria": "proveedor", "valor": proveedor_valido})

        return atributos_validos
    except Exception as e:
        print(f"[attr_extract] Error: {e}")
        return []
