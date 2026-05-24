import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from Modelfiles import CualifiquerIntent
from Modelfiles import CreateProduct
from Modelfiles import ValueResolver
from Modelfiles import ValueExtractor
from Modelfiles import ValueClassifier
from Modelfiles import IncompletHandler
from Modelfiles import IncreaseDetector
from Modelfiles import GeneralConsultant

load_dotenv()

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
OLLAMA_BASE_URL = "http://localhost:11434"

def get_llm():
    return OllamaLLM(
        model=DEFAULT_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

def get_intent():
    return OllamaLLM(
        model=CualifiquerIntent,
        base_url=OLLAMA_BASE_URL
    )

def get_create_product():
    return OllamaLLM(
        model=CreateProduct,
        base_url=OLLAMA_BASE_URL
    )

def get_value_extractor():
    return OllamaLLM(
        model=ValueExtractor, 
        base_url=OLLAMA_BASE_URL
    )

def get_value_classifier():
    return OllamaLLM(
        model=ValueClassifier, 
        base_url=OLLAMA_BASE_URL
    )

def get_value_resolver():
    return OllamaLLM(
        model=ValueResolver,
        base_url=OLLAMA_BASE_URL
    )

def get_incomplete_handler():
    return OllamaLLM(
        model=IncompletHandler,
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
