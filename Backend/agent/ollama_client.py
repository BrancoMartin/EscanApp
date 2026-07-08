import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

load_dotenv()

OLLAMA_BASE_URL = "http://localhost:11434"

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
    return OllamaLLM(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b"),
        base_url=OLLAMA_BASE_URL
    )

def get_intent():
    return OllamaLLM(
        model=Intent,
        base_url=OLLAMA_BASE_URL
    )

def get_create_product():
    return OllamaLLM(
        model=CreateProduct,
        base_url=OLLAMA_BASE_URL
    )

def get_attribute_extractor():
    return OllamaLLM(
        model=AttributeExtractor,
        base_url=OLLAMA_BASE_URL
    )

def get_attribute_classifier():
    return OllamaLLM(
        model=AttributeClassifier,
        base_url=OLLAMA_BASE_URL
    )

def get_attribute_resolver():
    return OllamaLLM(
        model=AttributeResolver,
        base_url=OLLAMA_BASE_URL
    )

def get_incomplete_handler():
    return OllamaLLM(
        model=IncompleteHandler,
        base_url=OLLAMA_BASE_URL
    )

def get_increase_detector():
    return OllamaLLM(
        model=IncreaseDetector,
        base_url=OLLAMA_BASE_URL
    )

def get_general_consultant():
    return OllamaLLM(
        model=GeneralConsultant,
        base_url=OLLAMA_BASE_URL
    )

def create_categories_by_products():
    return OllamaLLM(
        model=CreateCategories,
        base_url=OLLAMA_BASE_URL
    )
