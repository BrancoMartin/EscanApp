## Why

**Crear un producto a mano tarda ~13 segundos en confirmar.** El usuario completa el formulario, aprieta "Guardar producto" y el mensaje "Producto creado: X" no aparece hasta 13 segundos después. El producto ya está guardado en la base desde el primer instante: lo que el usuario espera es trabajo de IA que ni siquiera ve en pantalla.

`POST /api/products/` invoca **dos modelos Ollama en serie** antes de responder:

```python
created_categories = create_categories(...)      # modelo 1
result = attribute_extractor(...)                # modelo 2
return productCreate                             # recién acá responde
```

Medido en la máquina real (i3-1115G4, 2 núcleos, sin GPU):

| Llamada | Tiempo |
|---|---|
| `create_categories` | 7.57 s |
| `attribute_extractor` | 5.29 s |
| **Total de IA dentro del POST** | **12.85 s** |

Esto viola dos reglas ya establecidas del proyecto:

1. **"Máximo 1 modelo por request"** (SDD `ai-agent`, presupuesto de latencia). Con 7.7 GB de RAM Ollama sostiene un solo modelo residente: el segundo expulsa al primero y lo recarga de disco. Los dos modelos en serie son el peor caso posible.
2. El endpoint **duplica, peor, lógica que ya existe**. El agente hace este mismo enriquecimiento en `_enriquecer_producto_con_atributos` (`controller_agent.py`), que ya está optimizado (change `optimize-agent-latency`, tarea 4.3): garantiza la categoría `proveedor` determinísticamente y llama a `create_categories` **solo si** `attribute_extractor` no devolvió nada. Es decir: **1 modelo en vez de 2**. El POST del formulario nunca recibió esa optimización, así que un producto creado por el formulario y el mismo producto creado por el chat siguen caminos distintos.

**Además, el alta de producto no distingue si el código de barras se tecleó o se escaneó.** La pantalla de escaneo (`ScanProductsOption.jsx`) ya mide el intervalo entre teclas para distinguir el lector (ráfaga <50 ms) del tecleo manual, y usa esa señal para auto-enviar solo cuando fue el lector. Esa conducta **está implementada pero no está escrita en ningún SDD**, y el formulario de alta no la tiene. Tener la señal visible en el alta le sirve al usuario para probar los dos caminos de entrada.

## What Changes

- **El mensaje de éxito deja de esperar a la IA.** `POST /api/products/` SHALL responder apenas el producto está persistido. El enriquecimiento (categorías + atributos) SHALL ejecutarse después, en un hilo daemon, sin bloquear la respuesta. El contrato HTTP no cambia: mismo endpoint, mismo body, mismos códigos de error.
- **Un solo modelo por creación.** El POST SHALL reusar el mismo enriquecimiento que usa el agente, en vez de su propia copia con dos modelos. Un producto creado por el formulario y uno creado por el chat SHALL quedar enriquecidos igual.
- **Hogar correcto para el enriquecimiento.** La lógica se extrae de `controller_agent.py` a `Backend/services/product_enrichment_service.py`, respetando la arquitectura en capas del proyecto (API → Services → Repositories → Models). Hoy vive en un módulo de rutas y el otro módulo de rutas no puede reusarla sin importar una función privada.
- **El alta de producto distingue tecleo de escaneo**, con el mismo criterio que ya usa la pantalla de escaneo, y lo muestra como un indicador discreto en el campo.
- **Se documenta en el SDD la detección lector/manual que ya existe** en la pantalla de escaneo (hueco de documentación: código sin spec).

## Capabilities

### Modified Capabilities
- `products`: crear un producto responde de inmediato; el enriquecimiento por IA pasa a segundo plano y usa un solo modelo.
- `ui`: el formulario de alta confirma sin demora y distingue código tecleado de código escaneado; se documenta la detección de lector ya existente en la pantalla de escaneo.

## Impact

- `Backend/services/product_enrichment_service.py` — **nuevo**. Enriquecimiento de producto (atributos existentes + `attribute_extractor`, con `create_categories` solo como fallback) y los helpers de comparación de texto que necesita.
- `Backend/api/routes/controller_agent.py` — deja de definir el enriquecimiento y lo importa del servicio. Los helpers se importan con alias para no tocar los ~100 puntos de uso existentes.
- `Backend/api/routes/controller_products.py` — `create` responde apenas persiste y dispara el enriquecimiento en un hilo daemon con su propia sesión de base.
- `Frontend/src/Components/AddProduct/AddProductOption.jsx` + `.css` — detección lector/manual e indicador.
- **No cambia** el contrato HTTP ni la base de datos.
- **Riesgo asumido:** el enriquecimiento pasa a ser asíncrono, así que los atributos de un producto recién creado pueden tardar unos segundos en aparecer. Es aceptable: hoy ninguna pantalla los muestra inmediatamente después de crear, y el usuario ya esperaba a que la IA los infiriera igual.
- El hilo daemon usa `threading`, patrón ya establecido en el proyecto (`warmup()` del agente y el aprovisionamiento de Ollama en el arranque ya corren así).
