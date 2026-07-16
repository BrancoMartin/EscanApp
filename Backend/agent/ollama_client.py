import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

from Backend.agent.provisioning import BASE_MODEL

load_dotenv()

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434"
)

# Mantiene cada modelo cargado en memoria por este tiempo tras usarlo, para no
# pagar la recarga (~2.2s por modelo en CPU) en el proximo request.
#
# OJO: la variable se llama AGENT_KEEP_ALIVE a proposito. La maquina de
# ejecucion tiene OLLAMA_KEEP_ALIVE=0 en el entorno (default del servidor:
# descargar el modelo apenas responde). Si leyeramos ESE nombre, tomariamos el
# "0" y le pediriamos a Ollama que descargue el modelo tras cada llamada. El
# keep_alive que mandamos por request sobrescribe el default del servidor.
KEEP_ALIVE = os.getenv("AGENT_KEEP_ALIVE", "30m")

# Identificadores de los 9 modelos especializados (tags de Ollama, creados con
# `ollama create <tag> -f Modelfiles/<Nombre>`). Los parametros de generacion
# (temperature, num_predict, etc.) viven dentro de cada Modelfile.
Intent = "cualifiquer-intent"
CreateProduct = "create-product"
AttributeExtractor = "attribute-extractor"
AttributeClassifier = "attribute-classifier"
AttributeResolver = "attribute-resolver"
IncompleteHandler = "incomplet-handler"
IncreaseDetector = "increase-detector"
GeneralConsultant = "general-consultant"
CreateCategories = "create-categories-by-products"


def get_llm():
    # El default sale de provisioning.BASE_MODEL, que es el mismo modelo que
    # declara el FROM de los 9 Modelfiles y el unico que el instalador descarga.
    # Apuntar OLLAMA_MODEL a otro modelo significa bajarse un modelo entero que
    # la app no usa (era el caso: el .env pedia gemma3:4b, 3.3 GB al pedo).
    return OllamaLLM(
        model=os.getenv("OLLAMA_MODEL", BASE_MODEL),
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def get_intent():
    return OllamaLLM(
        model=Intent,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def get_create_product():
    return OllamaLLM(
        model=CreateProduct,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def get_attribute_extractor():
    return OllamaLLM(
        model=AttributeExtractor,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def get_attribute_classifier():
    return OllamaLLM(
        model=AttributeClassifier,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def get_attribute_resolver():
    return OllamaLLM(
        model=AttributeResolver,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def get_incomplete_handler():
    return OllamaLLM(
        model=IncompleteHandler,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def get_increase_detector():
    return OllamaLLM(
        model=IncreaseDetector,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def get_general_consultant():
    return OllamaLLM(
        model=GeneralConsultant,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )

def create_categories_by_products():
    return OllamaLLM(
        model=CreateCategories,
        base_url=OLLAMA_BASE_URL,
        keep_alive=KEEP_ALIVE
    )


def warmup():
    """Precarga el modelo de intent en memoria al arrancar el backend, para que
    el primer mensaje del usuario no pague la carga del modelo (~2.2s en CPU).
    Un prompt vacio hace que Ollama solo cargue el modelo, sin generar."""
    try:
        get_intent().invoke("")
        print(f"[AGENT] Modelo '{Intent}' precargado (keep_alive={KEEP_ALIVE})")
    except Exception as e:
        print(f"[AGENT] Warmup fallido (Ollama no disponible?): {e}")
