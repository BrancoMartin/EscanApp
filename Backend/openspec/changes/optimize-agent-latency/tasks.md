## 1. Residencia de modelos (keep_alive)

- [x] 1.1 `ollama_client.py`: dejar de leer `OLLAMA_KEEP_ALIVE` (vale `0` en la máquina y descarga el modelo al instante); usar `AGENT_KEEP_ALIVE` con default `30m`
- [x] 1.2 `ollama_client.py`: función `warmup()` que precarga el modelo de intent
- [x] 1.3 `app.py`: invocar `warmup()` en un thread daemon al crear la app

## 2. Modelo base y presupuesto de generación (Modelfiles)

- [x] 2.1 Reconstruir `attribute-extractor` desde `qwen2.5:0.5b` — el tag instalado era un 3b de 1.9 GB (**27.0 s** por llamada); ahora pesa 397 MB
- [x] 2.2 Recortar el prompt de sistema de `AttributeExtractor`: 435 → **225 tokens** (a 144 tok/s de prompt eval en frío, son ~1.5 s menos por llamada)
- [x] 2.3 Recortar el prompt de `AttributeClassifier`: 258 → **222 tokens**
- [x] 2.4 Acotar `num_predict`: GeneralConsultant 200→48, CreateProduct 250→120, AttributeResolver 200→60, AttributeExtractor 150→48, IncompletHandler 80→50, CreateCategories 80→40, AttributeClassifier 60→30
- [x] 2.5 Agregar `num_ctx` acotado a todos los Modelfiles (menos RAM residente por modelo)
- [x] 2.6 NO tocar `IncreaseDetector` (ya optimizado). `CualifiquerIntent` solo recibió `num_ctx` (velocidad/memoria; no altera prompt ni sampling)
- [x] 2.7 Reconstruir los tags afectados con `ollama create`
- [x] 2.8 Reparar el encoding de `GeneralConsultant` (los acentos se habían corrompido al reescribirlo)

## 3. Fast-paths determinísticos de intent (controller_agent.py)

- [x] 3.1 Fast-path `listar_categorias` (verbo de listar + categoria/atributo)
- [x] 3.2 Fast-path `crear_categoria` (verbo de creación + "categoria")
- [x] 3.3 Fast-path `agregar_atributo` (verbo de creación/agregado + "atributo")
- [x] 3.4 Fast-path `crear_productos` (verbo de creación + "producto"/"articulo")
- [x] 3.5 Desempate por posición: gana el sustantivo que aparece PRIMERO en el mensaje
- [x] 3.6 Ruta directa a `consulta_general` para preguntas puras (sin verbos de gestión, ni %, ni sustantivos de creación/listado) — evita el modelo de intent
- [x] 3.7 Mover la detección de asignación producto→atributo ANTES de clasificar (antes se clasificaba y esa llamada se descartaba)
- [x] 3.8 Mantener el clasificador Ollama como red de seguridad para lo que no matchee (incluye precios sin verbo imperativo)

## 4. Un solo modelo por request

- [x] 4.1 `crear_productos`: invocar `CreateProduct` solo si la extracción determinística no obtiene el nombre
- [x] 4.2 `agregar_atributo`: auto-asignar productos con ILIKE; `AttributeResolver` sale del flujo (costaba ~10 s y hacía por inferencia un matching de texto). Si no hay coincidencias, PREGUNTAR
- [x] 4.3 `_enriquecer_producto_con_atributos`: garantizar la categoría `proveedor` determinísticamente; `CreateCategories` solo si `AttributeExtractor` no devuelve atributos
- [x] 4.4 Rescatar el JSON truncado de `AttributeExtractor` (un truncado disparaba el fallback a un 2º modelo: 19 s)
- [x] 4.5 Acotar a 3 los atributos aceptados y a 12 las categorías enviadas al modelo (emitía un atributo inventado por cada categoría existente)

## 5. Verificación

- [x] 5.1 Test offline del enrutado de intents (sin Ollama): 29/29 casos OK, 26/29 resueltos sin modelo
- [x] 5.2 Benchmark end-to-end por flujo contra `/api/agent/chat` (backend levantado sobre una copia de `pos.db`; base original restaurada al terminar)
- [x] 5.3 Confirmado: el flujo de aumento/disminución de precios sigue en ~0.01 s y correcto (no regresionó)

## 6. Calidad: la app decide y los datos son reales

- [x] 6.1 `agregar_atributo`: la APP decide sola a qué productos corresponde el atributo. Ya NO se le pregunta al usuario
- [x] 6.2 Matching determinístico mejorado: sin acentos y por raíz ("galletas" encuentra "Galleta rellena"; "plastico" encuentra "plástico")
- [x] 6.3 Al crear un producto, se lo vincula solo a los atributos existentes que menciona (hace verdad la promesa de "se lo asigno a los que crees después")
- [x] 6.4 `AttributeResolver` descartado con evidencia: dijo que "Martillo" es un lácteo y que "Pipas" es una golosina. Asignaría atributos equivocados en silencio
- [x] 6.5 Las preguntas factuales (cuántos productos, más caro/barato, promedio, ventas de hoy/semana/mes) las responde la BD: exactas y en ~0.01 s
- [x] 6.6 `_construir_stats`: el asesor ahora recibe productos con precio y ventas reales. Antes solo recibía conteos y categorías, y por eso decía "no tengo acceso a las ventas" y que el producto más caro era 'material' (una categoría)
- [x] 6.7 Quitados los números de ejemplo del prompt del asesor: los copiaba ("3 ventas por $6000" con UNA venta en la base)

## 7. Bug crítico encontrado y corregido (destruía datos)

- [x] 7.1 **"me conviene subir los precios?" aumentaba TODOS los precios un 100%.** El clasificador lo mandaba a `ajustar_precios`, `IncreaseDetector` inventaba `porcentaje: 100` y se aplicaba
- [x] 7.2 Red de seguridad: si el mensaje no tiene NINGÚN dígito, el porcentaje del modelo se descarta y se pide el porcentaje
- [x] 7.3 Las preguntas de opinión sobre precios ("me conviene…", "debería…", "?") se enrutan a `consulta_general`, no a una orden de ajuste
- [x] 7.4 Verificado: las órdenes reales siguen funcionando ("aumentame todos un 10%" → 0.03 s)

## Resultado medido (i3-1115G4, 2 núcleos, sin GPU)

| Flujo | Antes | Ahora | Modelos |
|---|---|---|---|
| Ajustar precios (aumento/disminución) | 0.01 s | **0.01 s** (sin cambios) | 0 |
| Listar categorías | ~4 s | **0.02 s** | 0 |
| Crear categoría | ~4 s | **0.01 s** | 0 |
| Agregar atributo (categoría explícita) | ~10 s | **0.02 s** | 0 |
| Consulta factual (productos, precios, ventas) | 7–12 s **y con datos falsos** | **0.01 s y exacta** | 0 |
| Agregar atributo (categoría inferida) | ~16 s | **4.1 s** | 1 |
| Crear producto (paso final) | **27 s** | **4.8 s** | 1 |
| Pregunta abierta de criterio | 7–12 s | **~9 s** | 1 |

## Decidido por el usuario

- [x] `AttributeResolver` fuera del flujo: la app decide sola, sin preguntarle al comerciante
- [x] Preguntas de criterio: se acepta que el 0.5b improvise (a veces incoherente). Las factuales, que son la mayoría, ya salen exactas de la BD
- [ ] Opcional a futuro: consolidar los 9 tags de Ollama en UNO solo (mismo `qwen2.5:0.5b`, system prompt por llamada) eliminaría la recarga de ~1.4 s al alternar flujos. Contradice el requirement "9 modelos especializados"
