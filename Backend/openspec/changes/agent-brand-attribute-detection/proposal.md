## Why

**El agente crea atributos de marca inconsistentes, y a veces crea atributos con valor `none`.**

El almacenero carga golosinas y galletitas todo el día. La marca es el atributo que más importa para después ajustar precios ("aumentame todo lo de Arcor un 10%"), pero hoy el `AttributeExtractor` (qwen2.5:0.5b) es el único que decide si algo es marca, y falla de dos formas:

1. **No reconoce marcas conocidas de forma confiable.** "Milka", "Arcor", "Georgalos" aparecen escritos en el nombre o la descripción y el 0.5b a veces las clasifica como `tipo`, a veces las omite, a veces las deforma. La misma marca termina cargada distinto en dos productos, y el ajuste por atributo no los agrupa.

2. **No distingue un adjetivo (descripción del producto) de un sustantivo propio (marca).** "chocolatado", "relleno", "grande" son características; "Milka", "Felfort" son marcas. El 0.5b los mezcla.

3. **Sigue emitiendo valores basura.** El wrapper ya filtra `SINONIMOS_NULL` a nivel categoría y valor, pero el modelo todavía inventa atributos con valor `none`/`ninguno` cuando no hay nada claro. La red determinística tiene que ser la que garantice que **nunca** se persista un atributo con valor nulo o sinónimo de nulo.

Esto viola el requirement transversal del SDD **"Preferir preguntar antes que especular"**: un dato que el usuario escribió literal (el nombre de una marca argentina conocida) queda a merced de la inferencia de un 0.5b, en vez de resolverse determinísticamente.

## What Changes

- **Semilla determinística de marcas.** El sistema SHALL mantener una lista de marcas conocidas del rubro (kiosco/almacén argentino). Si alguna aparece —como palabra completa— en el nombre o la descripción del producto, el sistema SHALL emitir determinísticamente `{"categoria":"marca","valor":<marca canónica>}`, sin depender de la salida del modelo, con la marca normalizada a su forma canónica (mismo criterio que la red de seguridad de `proveedor` ya existente).
- **Nunca un atributo con valor nulo.** El sistema SHALL garantizar, en la capa determinística, que ningún atributo persistido tenga `valor` vacío ni sinónimo de nulo (`none`, `ninguno`, `n/a`, `-`, etc.), sin importar lo que devuelva el modelo.
- **Guía adjetivo vs. sustantivo propio.** El `AttributeExtractor` SHALL orientarse (vía prompt del Modelfile) a tratar un sustantivo propio suelto (capitalizado, sin ser adjetivo descriptivo) como candidato a `marca`, y un adjetivo descriptivo como atributo de característica (`tipo`, `material`, `sabor`, etc.), no como marca.

## Capabilities

### Modified Capabilities
- `ai-agent`: la extracción de atributos gana una semilla determinística de marcas conocidas y una garantía dura de que nunca se persiste un atributo con valor nulo.

## Impact

- `Backend/agent/model_attribute_extractor.py` — lista de marcas canónicas + red de seguridad determinística que inyecta el atributo `marca` cuando la detecta en nombre/descripción, y que descarta cualquier valor nulo/sinónimo antes de retornar.
- `Modelfiles/AttributeExtractor` — el `SYSTEM` gana guía de adjetivo vs. sustantivo propio y ejemplos de marca. **Requiere reconstruir el tag** con `ollama create` (ver `crear_modelos.bat`).
- **No cambia** el contrato del endpoint `/api/agent/chat`.
- La detección de marca por semilla corre sin llamar al modelo: no agrega latencia.
