## Why

El agente de IA del chat responde mal en la mayoría de los casos de uso reales. La causa raíz es que los Modelfiles evolucionaron hacia un diseño de **ajuste de precios** (aumento *y* disminución, intent `ajustar_precios`) pero ni el SDD `ai-agent` ni el controlador (`controller_agent.py`) acompañaron ese cambio:

- El Modelfile `CualifiquerIntent` devuelve `ajustar_precios`, pero el controlador compara contra `aumentar_precios` → **nunca coincide** y todo pedido de precios cae en "consulta general".
- El Modelfile `IncreaseDetector` ya devuelve `operacion: aumento|disminucion`, pero el controlador ignora ese campo y siempre aumenta → "bajame la leche 10%" *aumentaría* el precio.
- El clasificador no emite `listar_categorias`, dejando esa rama muerta.
- Varios wrappers de modelo violan requisitos de gobernanza que YA están en el SDD (`_cached()` en `ollama_client.py`; `frozenset` + list comprehension en `model2a`/`model3`).
- El flujo de creación de producto no invoca `CreateCategories` para la categoría `proveedor` como describe el SDD.

## What Changes

- **Renombrar el intent** de precios de `aumentar_precios` a `ajustar_precios` en el SDD (alineado a los Modelfiles).
- **Generalizar el ajuste de precios** a dos operaciones: `aumento` (`precio * (1 + %/100)`) y `disminucion` (`precio * (1 - %/100)`), respetando el campo `operacion` de `IncreaseDetector`.
- Formalizar los **4 tipos de destino**: `todos`, `individual`, `por_atributo`, `por_categoria`, para ambas operaciones.
- Formalizar el **wiring del controlador**: mapear el intent del clasificador y aplicar la operación correcta, con mensajes que digan "aumentó" o "disminuyó" según corresponda.
- Formalizar que el clasificador **SHALL emitir `listar_categorias`**.
- Dar un rol real a `IncompleteHandler`: **fallback determinístico** dentro de `consulta_general` cuando el mensaje contiene un verbo de acción pero está incompleto (los faltantes de flujos concretos siguen inline, sin modelo).
- (Solo código, ya especificado) Corregir violaciones de gobernanza: `ollama_client.py` sin `_cached()`; `model2a`/`model3` sin `frozenset`.

## Capabilities

### Modified Capabilities
- `ai-agent`: el dominio de precios pasa de "aumento" a "ajuste" (aumento + disminución) y se corrige el contrato de intent/controlador y el listado de categorías.

## Impact

- `Backend/api/routes/controller_agent.py` — mapear intent `ajustar_precios`, aplicar `operacion`, wording dinámico, ramas de tipo completas.
- `Backend/agent/ollama_client.py` — reescribir sin `_cached()` (gobernanza SDD).
- `Backend/agent/model2a_create_product.py`, `Backend/agent/model3_detect_attr.py` — limpieza de nulos con `SINONIMOS_NULL` + `for` (gobernanza SDD).
- `Modelfiles/CualifiquerIntent` — agregar `listar_categorias`.
- No cambia base de datos ni contrato HTTP del endpoint `/api/agent/chat`.
- Tras editar Modelfiles, se debe reconstruir con `ollama create`.
