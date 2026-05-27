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

# CUALIFIQUER INTENT 
# Identifica la intencion del usuario y devuelva la accion que tiene que ejecutar este: ejemplo aumentar_precios, 
# crear_categoria etc.
def get_intent():
    return OllamaLLM(
        model=CualifiquerIntent,
        base_url=OLLAMA_BASE_URL
    )

#CREATE PRODUCT
# SIRVE PARA QUE EL MODELO EN BASE A UN PROMPT DEL USUARIO ME DEVUEVA LISTOS LOS CAMPOS 
# PARA QUE YO PUEDA CREAR UN PRODUCTO
# si uno de los campos para crear el producto es null: ejemplo: nombre del producto, barcode, descripcion, 
# precio que tire null en un campo entonces despues con logica le digo que falta ese campo y que lo vuelva 
# a ingresar y ahi si que cree el producto.
def get_create_product():
    return OllamaLLM(
        model=CreateProduct,
        base_url=OLLAMA_BASE_URL
    )

#VALUE EXTRACTOR
#ESTE SE GENERA CUANDO SE CREA UN PRODUCTO Y ES PARA QUE DETECTE LOS VALUES INGRESADOS Y GENERE LA CATEGORIA Y EL VALOR
def get_value_extractor():
    return OllamaLLM(
        model=ValueExtractor, 
        base_url=OLLAMA_BASE_URL
    )

#VALUE CLASSIFIQUER
#ESTE SE EJECUTA CUANDO EL USUARIO QUIERE AUMENTAR ALGO EL MODELO DEVUELVE EL VALOR, Y LA CATEGORIA PARA POSTERIORMENTE HACER EL AUMENTO

def get_value_classifier():
    return OllamaLLM(
        model=ValueClassifier, 
        base_url=OLLAMA_BASE_URL
    )


# VALUE RESOLVER 
# ESTE SE PODRIA USAR CUANDO CREAMOS UN VALUE, EJEMPLO "PLASTICO" Y LUEGO LE PASAMOS LOS PRODUCTOS Y CATEGORIAS PARA 
# QUE DETERMINE QUE PRODUCTOS POSEEN ESE VALOR Y A QUE CATEGORIA PERTENECE ESE VALUE
# o también se podria crear en el caso de que ya tengamos creados productos y categorias en la db y querramos pasarselo a este modelo para que determine que productos poseen ese value y a que categoria pertenece ese value
def get_value_resolver():
    return OllamaLLM(
        model=ValueResolver,
        base_url=OLLAMA_BASE_URL
    )


# INCOMPLETE HANDLER
#ESTE SE EJECUTA CUANDO EL USUARIO HACE UN PROMPT AL CUAL LE FALTA INFORMACION Y EL MODELO LE DA UNA RESPUESTA INDICANDOLE LO QUE HACE FALTA PARA REALIZAR UNA ACCION
def get_incomplete_handler():
    return OllamaLLM(
        model=IncompletHandler,
        base_url=OLLAMA_BASE_URL
    )


# INCREASE DETECTOR
# DETECTA EL TIPO DE AUMENTO QUE EL USUARIO QUIERE HACER OSEA todos, por valor, por producto
def get_increase_detector():
    return OllamaLLM(
        model=IncreaseDetector,
        base_url=OLLAMA_BASE_URL
    )

# GENERAL CONSULTANT
# RESPONDE LAS DUDAS DEL USUARIO EN MODO ASESOR FINANCIERO
def get_general_consultant():
    return OllamaLLM(
        model=GeneralConsultant,
        base_url=OLLAMA_BASE_URL
    )
