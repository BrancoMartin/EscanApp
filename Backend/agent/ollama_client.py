import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from Modelfiles import CualifiquerIntent
from Modelfiles import CreateProduct
from Modelfiles import AttributeResolver
from Modelfiles import AttributeExtractor
from Modelfiles import AttributeClassifier
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
