## Why

El SDD `ai-agent` ya exige **respuesta en ≤ 3.5 s** ("Requirement: Performance — respuesta máxima en 3.5 segundos"), pero el agente lo incumple en todos los flujos salvo el de ajuste de precios (aumento/disminución), que ya fue optimizado con fast-paths determinísticos.

Mediciones sobre el hardware real de ejecución (Intel i3-1115G4, 2 núcleos físicos, sin GPU dedicada, 7.7 GB de RAM → Ollama corre **100% en CPU a ~27 tokens/s**):

| Causa medida | Impacto |
|---|---|
| El tag `attribute-extractor` instalado en Ollama pesa **1.9 GB**: fue creado desde `qwen2.5:3b` y nunca se reconstruyó tras cambiar el Modelfile a `FROM qwen2.5:0.5b` | **27.0 s** por llamada (14.1 s carga + 8.5 s prompt + 4.4 s generación). Se invoca en CADA creación de producto |
| La variable de entorno del sistema `OLLAMA_KEEP_ALIVE=0` es leída por `ollama_client.py` (`os.getenv("OLLAMA_KEEP_ALIVE", "30m")`), por lo que el cliente le pide a Ollama **descargar el modelo apenas responde** | +2.2 s de recarga desde disco en CADA llamada. Mismo modelo/consulta: **5.13 s en frío vs 0.66 s en caliente** |
| `num_predict` alto en CPU a 27 tok/s: `GeneralConsultant`=200, `CreateProduct`=250, `AttributeResolver`=200 | 200 tokens = **7.4 s solo generando**, antes de sumar carga y prompt |
| Varios flujos encadenan 2–3 modelos DISTINTOS por request (ej. crear producto = intent + CreateProduct + CreateCategories + AttributeExtractor) | Cada modelo distinto es una carga/swap adicional; con 2 núcleos y 7.7 GB no caben los 9 residentes |
| `AttributeResolver` recibe **la lista completa de productos** en el prompt para hacer un matching por nombre/descripción que la BD resuelve con un ILIKE | Prompt que crece con el inventario; trabajo de inferencia que no requiere inferencia |

La causa raíz común: se usa un modelo para trabajo que NO requiere inferencia genuina, lo cual **ya está prohibido** por el requirement "Preferir preguntar antes que especular" ("Los modelos SHALL usarse solo para lo que requiere inferencia genuina"). Este change extiende a los demás flujos la misma estrategia que ya hizo rápido y confiable al de precios.

## What Changes

- **Presupuesto de latencia explícito en el SDD**: cada flujo SHALL invocar **como máximo 1 modelo** en su camino común (el de precios ya invoca 0), y el objetivo de respuesta pasa a estar entre **3 y 5 s** en el peor caso, con ≤ 3.5 s como objetivo del camino común.
- **`keep_alive` de modelos**: el cliente SHALL mantener los modelos residentes entre requests y NO SHALL leer la variable `OLLAMA_KEEP_ALIVE` (que en la máquina de ejecución vale `0` y provoca la descarga inmediata). Se usa una variable propia `AGENT_KEEP_ALIVE`.
- **Fast-paths determinísticos de intent** para `listar_categorias`, `crear_categoria`, `agregar_atributo` y `crear_productos`, igual que el que ya existe para `ajustar_precios`. El clasificador Ollama queda como red de seguridad para lo ambiguo (y sigue cubriendo el caso de precios sin verbo imperativo).
- **Modelos degradados a fallback** (dejan de estar en el camino común, siguen definidos e invocables):
  - `CreateProduct`: solo si la extracción determinística no logra sacar el nombre del producto.
  - `AttributeResolver`: solo si el matching determinístico (ILIKE por nombre/descripción) no encuentra ningún producto — es decir, solo para el caso que SÍ requiere inferencia semántica (ej. "lácteos" → "leche entera").
  - `CreateCategories`: solo si `AttributeExtractor` no devuelve ningún atributo. La categoría `proveedor` se garantiza determinísticamente (el wrapper ya lo hacía como red de seguridad).
- **Presupuesto de generación por modelo**: `num_predict` acotado a lo que el formato de salida realmente necesita, y `num_ctx` acotado para reducir la RAM residente por modelo.
- **Precarga en el arranque** del backend: el modelo de intent se carga en segundo plano al levantar la app, para que el primer mensaje del usuario no pague la carga.
- **`AttributeExtractor` reconstruido desde `qwen2.5:0.5b`** (lo que el Modelfile ya declara) con el prompt de sistema recortado.

## Capabilities

### Modified Capabilities
- `ai-agent`: se formaliza el presupuesto de latencia por flujo, el rol de cada modelo (camino común vs. fallback) y la residencia de modelos en memoria.

## Impact

- `Backend/agent/ollama_client.py` — `keep_alive` propio (deja de leer `OLLAMA_KEEP_ALIVE`) + función de precarga.
- `Backend/api/routes/controller_agent.py` — fast-paths de intent; `CreateProduct`, `AttributeResolver` y `CreateCategories` a fallback; matching determinístico de productos por atributo.
- `Backend/agent/model4_resolve_attr.py` — acota la lista de productos enviada al modelo.
- `Backend/api/app.py` — precarga del modelo de intent al arrancar.
- `Modelfiles/AttributeExtractor`, `AttributeClassifier`, `AttributeResolver`, `CreateCategories`, `CreateProduct`, `GeneralConsultant`, `IncompletHandler` — `num_predict` / `num_ctx` acotados.
- **NO se tocan** `Modelfiles/IncreaseDetector` ni la lógica de aumento/disminución de precios (ya optimizados). `Modelfiles/CualifiquerIntent` solo recibe `num_ctx` (parámetro de velocidad/memoria; no altera el prompt ni el sampling).
- Requiere reconstruir los tags afectados con `ollama create <tag> -f Modelfiles/<Nombre>`.
- No cambia la base de datos ni el contrato HTTP de `/api/agent/chat`.
