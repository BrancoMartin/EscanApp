# AI Agent Domain

## Requirements

### Requirement: Detección de intención (Intent Classifier)

El sistema SHALL clasificar el mensaje del usuario en uno de los siguientes intents: aumentar_precios, crear_productos, crear_categoria, listar_categorias, agregar_atributo, info_incompleta, consulta_general.

#### Scenario: Intención de aumento de precios

- **WHEN** el usuario escribe "aumentame todos los productos un 15%" o "subime los precios"
- **THEN** el sistema detecta intent = "aumentar_precios"

#### Scenario: Intención de crear producto

- **WHEN** el usuario describe un nuevo producto
- **THEN** el sistema detecta intent = "crear_productos"

#### Scenario: Intención de consulta general

- **WHEN** el usuario pregunta "cuantos productos tengo?"
- **THEN** el sistema detecta intent = "consulta_general"

### Requirement: Aumento de precios por tipo

El sistema SHALL soportar tres tipos de aumento de precios: todos los productos, producto individual, por atributo.

#### Scenario: Aumentar todos los productos

- **WHEN** el usuario pide aumentar todos los productos un porcentaje
- **THEN** el sistema aplica precio = precio \* (1 + porcentaje / 100) a todos los productos
- **AND** retorna el conteo de productos actualizados

#### Scenario: Aumentar producto individual

- **WHEN** el usuario pide aumentar un producto específico por nombre
- **THEN** el sistema busca el producto por nombre con ILIKE
- **AND** aplica el aumento solo a ese producto

#### Scenario: Aumentar por atributo

- **WHEN** el usuario pide aumentar productos con un atributo específico
- **THEN** el sistema busca el atributo en la base de datos
- **AND** aplica el aumento solo a productos que tengan ese atributo

### Requirement: Flujo detallado de aumento por atributo con descubrimiento automático

Cuando el usuario pide aumentar precios por un atributo que no existe en la BD, el sistema SHALL usar múltiples agentes para descubrir, crear categorías, crear el atributo, y auto-asignar productos.

#### Scenario: Atributo existe directamente

- **WHEN** el usuario pide aumentar por un atributo que ya existe en la BD
- **THEN** el sistema busca productos vinculados a ese atributo vía ProductAttribute
- **AND** aplica el aumento a esos productos

#### Scenario: Atributo no existe — detectar categoría con agente

- **WHEN** el usuario pide aumentar por un atributo que NO existe en la BD
- **THEN** el sistema invoca el modelo detect_category_and_value para inferir a qué categoría pertenece
- **AND** si la categoría inferida no existe, la crea en la BD

#### Scenario: Atributo no existe sin categoría inferible

- **WHEN** el agente no puede inferir la categoría del atributo
- **THEN** el sistema busca un fallback por ILIKE en nombres de categorías existentes
- **AND** si encuentra una categoría similar, busca productos con atributos de esa categoría y aplica el aumento

#### Scenario: Atributo creado — auto-asignar productos existentes

- **WHEN** se crea un nuevo atributo
- **THEN** el sistema busca productos cuyo nombre o descripción contengan el valor del atributo
- **AND** asigna automáticamente el atributo a esos productos vía ProductAttribute
- **AND** aplica el aumento de precio a esos productos

#### Scenario: Atributo creado — sin productos detectados

- **WHEN** se crea un nuevo atributo pero no se encuentran productos automáticamente
- **THEN** el sistema retorna mensaje indicando que no encontró productos para asignar
- **AND** guarda el contexto para que el usuario pueda especificar manualmente qué productos vincular

### Requirement: Creación de productos vía chat

El sistema SHALL guiar al usuario en la creación de un producto mediante un flujo conversacional paso a paso: nombre, precio, código de barras.

#### Scenario: Flujo completo de creación

- **WHEN** el usuario indica querer crear un producto
- **THEN** el sistema solicita el nombre
- **AND** luego solicita el precio
- **AND** luego solicita el código de barras
- **AND** finalmente crea el producto con atributos inferidos

#### Scenario: Escaneo de barcode de producto no existente

- **WHEN** el usuario escanea un barcode no registrado
- **THEN** el sistema inicia el flujo de creación preguntando el nombre
- **AND** guarda el barcode como pendiente

#### Scenario: Producto duplicado por barcode

- **WHEN** el usuario completa la creación con un barcode ya existente
- **THEN** el sistema rechaza con mensaje "Ya existe un producto con ese codigo de barras"

### Requirement: Extracción de atributos por IA

El sistema SHALL extraer atributos (categoría + valor) del nombre y descripción de un producto usando el modelo attribute_extractor.

#### Scenario: Extracción al crear producto

- **WHEN** se crea un producto desde el chat
- **THEN** el sistema invoca attribute_extractor para inferir atributos
- **AND** crea categorías y atributos faltantes
- **AND** asocia los atributos al producto

#### Scenario: Enriquecimiento post-creación

- **WHEN** se crea un producto
- **THEN** el sistema invoca una segunda pasada de extracción para atributos adicionales
- **AND** asigna los nuevos atributos encontrados

### Requirement: Manejo de información incompleta

El sistema SHALL detectar cuando la solicitud del usuario tiene información faltante y solicitar los datos necesarios.

#### Scenario: Aumento sin especificar objetivo

- **WHEN** el usuario dice "aumentame los precios" sin especificar cuánto
- **THEN** el sistema solicita el porcentaje de aumento

#### Scenario: Aumento sin porcentaje

- **WHEN** el usuario dice "aumentame la leche" sin especificar porcentaje
- **THEN** el sistema solicita el porcentaje de aumento

### Requirement: Consultas generales de inventario

El sistema SHALL responder consultas generales sobre el estado del inventario: cantidad de productos, ventas del día, etc.

#### Scenario: Consultar cantidad de productos

- **WHEN** el usuario pregunta "cuantos productos tengo?"
- **THEN** el sistema consulta la base de datos
- **AND** retorna el conteo total de productos

#### Scenario: Consultar ventas

- **WHEN** el usuario pregunta "cuales fueron las ventas de hoy?" o "decime las ventas que tuve este mes" o "esta semana cuantos {producto} vendi?"
- **THEN** el sistema consulta las ventas
- **AND** retorna el resumen

### Requirement: 9 modelos especializados de IA

El sistema SHALL utilizar 9 modelos Ollama especializados, cada uno con un prompt específico para una tarea concreta.

#### Scenario: Modelos cargados

- **WHEN** el sistema inicia el agente
- **THEN** todos los modelos están disponibles para ser invocados según la intención detectada

### Requirement: Fábrica de LLM en ollama_client.py

El archivo `ollama_client.py` SHALL definir una función por cada modelo, y cada función SHALL instanciar `OllamaLLM` directamente con su modelo y `OLLAMA_BASE_URL`, sin usar helpers como `_cached()`.

#### Scenario: Formato de cada función

- **WHEN** se define una función para un modelo
- **THEN** la función SHALL tener este formato:

```python
def create_categories_by_products():
    return OllamaLLM(
        model=CreateCategories,
        base_url=OLLAMA_BASE_URL
    )
```

- **AND** cada función usa el identificador del modelo correspondiente (e.g. `CreateCategories`, `Intent`, `CreateProduct`, `AttributeExtractor`, `AttributeClassifier`, `AttributeResolver`, `IncompleteHandler`, `IncreaseDetector`, `GeneralConsultant`)
- **AND** todas las funciones reciben el mismo `base_url` desde la variable `OLLAMA_BASE_URL`
- **AND** ninguna función SHALL usar el patrón `_cached("...")`

### Requirement: Limpieza de valores nulos en respuestas de modelos

Los model files SHALL limpiar valores nulos/vacíos de las listas retornadas por los modelos usando una lista `SINONIMOS_NULL` con un bucle `for` explícito. NO SHALL usar `frozenset` con list comprehension.

#### Scenario: Formato correcto de limpieza

- **WHEN** un modelo retorna una lista con valores que pueden ser nulos
- **THEN** la función SHALL usar este formato:

```python
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

categorias_validas = []

for categoria in data.get("categorias_nuevas", []):
    nombre = categoria.get("nombre", "").strip().lower()

    if nombre not in SINONIMOS_NULL and nombre != "":
        categorias_validas.append(categoria)

data["categorias_nuevas"] = categorias_validas

return data
```

- **AND** NO SHALL usar `frozenset` con list comprehension como este patrón:

```python
# PROHIBIDO
_NULL_SYNONYMS = frozenset({ 'null', 'none', ... })
cats = data.get("categorias_nuevas", [])
if isinstance(cats, list):
    data["categorias_nuevas"] = [
        c for c in cats if isinstance(c, dict) and isinstance(c.get("nombre"), str)
        and c["nombre"].strip().lower() not in _NULL_SYNONYMS
    ]
```

### Requirement: Performance — respuesta máxima en 3.5 segundos

El sistema SHALL completar cualquier interacción del agente IA en un máximo de 3.5 segundos, desde que el usuario envía el mensaje hasta que recibe la respuesta.

#### Scenario: Respuesta dentro del límite

- **WHEN** el usuario envía un mensaje al agente
- **THEN** el sistema procesa (intent detection + acción + respuesta) en menos de 3.5s

#### Scenario: Timeout con feedback

- **WHEN** el procesamiento supera los 3.5s
- **THEN** el frontend muestra un mensaje de que el agente está tardando más de lo esperado
- **AND** permite al usuario reintentar o cancelar
