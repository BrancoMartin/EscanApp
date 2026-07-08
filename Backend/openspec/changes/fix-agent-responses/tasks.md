## 1. Controlador — enrutado y ajuste de precios

- [x] 1.1 Mapear el intent `ajustar_precios` (con alias `aumentar_precios`) en `controller_agent.py`
- [x] 1.2 Leer `operacion` de `detect_price_increase_type` y calcular el factor (`1 + %/100` o `1 - %/100`)
- [x] 1.3 Aplicar el factor en las 4 ramas: `todos`, `individual`, `por_atributo`, `por_categoria`
- [x] 1.4 Wording dinámico en los mensajes ("aumentó" / "disminuyó")
- [x] 1.5 Soportar `por_atributo` cuando el atributo es un proveedor

## 2. Listado de categorías

- [x] 2.1 Agregar `listar_categorias` al Modelfile `CualifiquerIntent`
- [x] 2.2 Verificar que el controlador ya maneja la rama `listar_categorias`

## 3. Gobernanza SDD (código existente)

- [x] 3.1 Reescribir `ollama_client.py` sin `_cached()`, una función por modelo con `OllamaLLM(...)` directo
- [x] 3.2 Reemplazar `frozenset` + list comprehension por `SINONIMOS_NULL` + `for` en `model2a_create_product.py`
- [x] 3.3 Ídem en `model3_detect_attr.py`

## 1b. Robustez determinística del ajuste de precios

- [x] 1b.1 Override de intent: verbo imperativo de precios → forzar `ajustar_precios` (o infinitivo + %)
- [x] 1b.2 Extraer porcentaje por regex si `IncreaseDetector` no lo devuelve
- [x] 1b.3 Derivar operación (aumento/disminución) del verbo del mensaje
- [x] 1b.4 Default `tipo = por_atributo` cuando hay objetivo pero el modelo no devolvió tipo
- [x] 1b.5 No disparar `info_incompleta` si el mensaje trae un porcentaje explícito
- [x] 1b.6 Test offline de la lógica de enrutado/parseo (sin Ollama)

## 3a. Crear producto — preguntar descripción y proveedor

- [x] 3a.1 Flujo conversacional como máquina de estados: nombre → precio → descripción → proveedor → barcode
- [x] 3a.2 Helpers `_es_negativo`, `_crear_producto_desde_data`, `_avanzar_creacion_producto` (sin duplicar lógica)
- [x] 3a.3 Descripción y proveedor opcionales, se preguntan siempre una vez, se omiten con "no"
- [x] 3a.4 No re-preguntar lo ya provisto explícitamente en el mensaje inicial
- [x] 3a.5 Mensaje final muestra descripción/proveedor si se cargaron
- [x] 3a.6 Simulación offline de la máquina de estados (4 escenarios)

## 3b. Crear producto — extracción determinística de datos

- [x] 3b.1 Helper `_parse_producto_deterministico` (nombre/precio/barcode/proveedor)
- [x] 3b.2 Overrides deterministicos sobre el resultado del modelo `CreateProduct`
- [x] 3b.3 Precio por marcador o número suelto (excluye barcode y cantidades)
- [x] 3b.4 Nombre conserva números internos legítimos (ej. "agua 2 litros")
- [x] 3b.5 Test offline del parser

## 3c. Crear categoría — extracción determinística del nombre

- [x] 3c.1 Helper `_limpiar_nombre_categoria` (fillers + cláusulas finales)
- [x] 3c.2 Fallback "agrupar/clasificar por X" cuando no dicen "categoria"
- [x] 3c.3 Test offline de la extracción

## 4d. Asignación manual de producto a atributo

- [x] 4d.1 Helper `_parse_asignar_producto_atributo` (ambos órdenes, verbo + producto + atributo)
- [x] 4d.2 Pre-check determinístico antes de clasificar intent
- [x] 4d.3 Buscar producto por ILIKE; error si no existe
- [x] 4d.4 Buscar atributo por ILIKE; crearlo (categoría inferida/`tipo`) si no existe
- [x] 4d.5 Crear vínculo ProductAttribute sin duplicar
- [x] 4d.6 Test offline del parser

## 0. Principio: preguntar antes que especular

- [x] 0.1 Requirement transversal "Preferir preguntar antes que especular" en el SDD
- [x] 0.2 Quitar la especulación del modelo `CreateProduct` en `agregar_atributo` (fuente del "Pepperoni") → preguntar si no hay valor determinístico

## 4e. Asignación: aceptar "categoria" como target y resolver con preguntas

- [x] 4e.1 Parser acepta `atributo` o `categoria` como target
- [x] 4e.2 Resolver target: atributo → asigna; categoría con 1 atributo → asigna
- [x] 4e.3 Categoría con 0/varios atributos → preguntar cuál
- [x] 4e.4 Target inexistente → preguntar si crear (no inventar)

## 4a. Agregado de atributo — extracción determinística del valor

- [x] 4a.1 Extraer el valor del atributo del mensaje (texto tras "atributo"), no del modelo
- [x] 4a.2 Solo usar `CreateProduct` como fallback si el mensaje no trae "atributo"
- [x] 4a.3 Categoría explícita ("de categoria X" / "de <cat existente>") + strip de "categoria"
- [x] 4a.4 No partir "galletas de chocolate" (split solo si es categoría explícita/existente)
- [x] 4a.5 Default de categoría `tipo` cuando no se puede inferir
- [x] 4a.6 Test offline de la extracción

## 4b. Fallback de información incompleta (IncompleteHandler)

- [x] 4b.1 Heurística determinística de verbos de acción en el controlador (lista blanca, palabra completa)
- [x] 4b.2 En la rama `consulta_general`: si hay verbo de acción, invocar `handle_incomplete_info` en vez del asesor general
- [x] 4b.3 Preservar el manejo inline de faltantes concretos (porcentaje, nombre, precio, barcode)

## 4. Creación de producto — proveedor

- [x] 4.1 Invocar `CreateCategories`/proveedor en el flujo de creación cuando venga proveedor informado
- [x] 4.2 Pasar `proveedor` al crear el `Product` en la rama `crear_productos` (se descartaba)
- [x] 4.3 Corregir que `AttributeExtractor` reciba la lista de categorías (no un string) para su lógica determinística de proveedor

## 5. Verificación

- [x] 5.1 Verificar sintaxis Python de todos los archivos tocados (`py_compile`)
- [x] 5.2 Repasar casos de uso: aumento/disminución × (todos, individual, por_atributo, por_categoria, proveedor)
- [ ] 5.3 Reconstruir Modelfiles modificados con `ollama create` (requiere entorno Ollama del usuario)
- [ ] 5.4 Prueba end-to-end del chat con Ollama corriendo (requiere entorno del usuario)
