import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

load_dotenv()

OLLAMA_BASE_URL = "http://localhost:11434"

_FAST_KWARGS = dict(temperature=0, num_predict=256)

_llm_cache: dict[str, OllamaLLM] = {}

def _cached(model: str) -> OllamaLLM:
    if model not in _llm_cache:
        _llm_cache[model] = OllamaLLM(model=model, base_url=OLLAMA_BASE_URL, **_FAST_KWARGS)
    return _llm_cache[model]

def get_llm():
    return _cached(os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b"))

def get_intent():
    return _cached("cualifiquer-intent")

def get_create_product():
    return _cached("create-product")

def get_attribute_extractor():
    return _cached("attribute-extractor")

def get_attribute_classifier():
    return _cached("attribute-classifier")

def get_attribute_resolver():
    return _cached("attribute-resolver")

def get_incomplete_handler():
    return _cached("incomplet-handler")

def get_increase_detector():
    return _cached("increase-detector")

def get_general_consultant():
    return _cached("general-consultant")

def create_categories_by_products():
    return _cached("create-categories-by-products")
