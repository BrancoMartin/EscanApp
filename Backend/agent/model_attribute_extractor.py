import json
import re
import unicodedata
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

# Marcas conocidas del rubro (kiosco/almacen argentino). La marca es el atributo
# que mas importa para el ajuste de precios por atributo, y el 0.5b la reconoce
# de forma inconsistente (a veces la omite, a veces la deforma, a veces la marca
# como "tipo"). Estas se detectan deterministicamente sobre nombre/descripcion,
# igual que la red de seguridad de "proveedor": el nombre de una marca escrito
# literal es un dato del usuario, no algo que deba inferir un modelo.
MARCAS_CONOCIDAS = [
    "Mondelez",
    "Arcor",
    "Terrabusi",
    "Milka",
    "Felfort",
    "Georgalos",
    "Bagley",
    "Guaymallén",
    "Jorgito",
    "Ferrero",
    "Nestlé",
    "Mars Wrigley",
    "Lheritier",
    "Billiken",
    "Tofi",
]


def _sin_acentos(texto: str) -> str:
    """Normaliza a minusculas y sin acentos, para comparar sin depender de como
    lo tipeo el usuario ("guaymallen" == "Guaymallén")."""
    nfkd = unicodedata.normalize("NFKD", str(texto or "").lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Indice normalizado -> forma canonica. Asi la misma marca escrita de dos formas
# distintas cae SIEMPRE en el mismo valor y el ajuste por atributo las agrupa.
_MARCAS_INDEX = {_sin_acentos(m): m for m in MARCAS_CONOCIDAS}


def _detectar_marcas(nombre: str, descripcion: str) -> list:
    """Devuelve las marcas canonicas que aparecen como palabra completa en el
    nombre o la descripcion. Sin invocar ningun modelo."""
    texto = _sin_acentos(f"{nombre or ''} {descripcion or ''}")
    encontradas = []
    for clave_norm, canonica in _MARCAS_INDEX.items():
        # \b no sirve con marcas de dos palabras / acentos ya removidos, pero un
        # limite de "no letra ni digito" alcanza para no matchear subcadenas.
        patron = r"(?<![0-9a-z])" + re.escape(clave_norm) + r"(?![0-9a-z])"
        if re.search(patron, texto) and canonica not in encontradas:
            encontradas.append(canonica)
    return encontradas


def _valor_es_nulo(valor: str) -> bool:
    """True si el valor esta vacio o es un sinonimo de nulo. Garantia dura: nunca
    se persiste un atributo con valor basura, venga del modelo o de una semilla."""
    v = str(valor or "").strip().lower()
    return v == "" or v in SINONIMOS_NULL


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
            if _valor_es_nulo(nombre_valor):
                continue
            atributos_validos.append({"categoria": nombre_categoria, "valor": nombre_valor})

        # Semilla deterministica de marcas: si una marca conocida aparece literal
        # en el nombre/descripcion, la inyectamos sin depender del 0.5b. Se guarda
        # con su forma canonica para que el ajuste por atributo agrupe siempre.
        # Va PRIMERO: la marca es el atributo mas valioso, no puede caerse en el
        # recorte a MAX_ATRIBUTOS si el modelo ya lleno el cupo con relleno.
        marcas_detectadas = _detectar_marcas(nombre, descripcion)
        marcas_ya = {m.lower() for m in marcas_detectadas}
        semilla_marcas = [{"categoria": "marca", "valor": m} for m in marcas_detectadas]
        resto = [
            a for a in atributos_validos
            if not (a["categoria"] == "marca" and a["valor"] in marcas_ya)
        ]

        atributos_validos = (semilla_marcas + resto)[:MAX_ATRIBUTOS]

        # Red de seguridad deterministica (SDD ai-agent): el proveedor lo escribio
        # el usuario, no hace falta que lo infiera un modelo.
        proveedor_valido = str(proveedor or "").strip().lower()
        categorias_existentes = [str(cat).strip().lower() for cat in (categoria or [])]

        if proveedor_valido not in SINONIMOS_NULL and proveedor_valido != "":
            # El valor que escribio el usuario es LA VERDAD, no una sugerencia
            # para el modelo. No alcanzaba con completarlo cuando el modelo lo
            # omitia: cuando SI lo emitia, lo emitia deformado. Con proveedor
            # "arcor" el 0.5b devolvia "acro" y "acor" -tres altas, tres valores
            # distintos-, asi que filtrar por proveedor no encontraba nada y la
            # base se llenaba de atributos basura. Se sobrescribe siempre.
            tiene_proveedor = False
            for attr in atributos_validos:
                if attr.get("categoria") == "proveedor":
                    attr["valor"] = proveedor_valido
                    tiene_proveedor = True

            if not tiene_proveedor and "proveedor" in categorias_existentes:
                atributos_validos.append({"categoria": "proveedor", "valor": proveedor_valido})

        return atributos_validos
    except Exception as e:
        print(f"[attr_extract] Error: {e}")
        return []
