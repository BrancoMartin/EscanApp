## Why

**Le mandás un código de barras al agente y te contesta el precio promedio de todos tus productos.**

El agente reconoce un código de barras **solo si el mensaje son puros dígitos y nada más**:

```python
bc_raw = user_message.strip()
if re.match(r"^\d{6,}$", bc_raw):     # <- solo si el mensaje ES el codigo, pelado
```

Alcanza con una palabra alrededor para que la detección no dispare. "que producto es el 7791234567890", "buscame el 7791234567890", "codigo 7791234567890" no matchean. Ese mensaje sigue de largo:

1. `_es_consulta_pura()` lo aprueba: no tiene verbo de acción, no tiene porcentaje, no nombra categoría ni atributo. → ruta directa a `consulta_general`.
2. `_responder_consulta_directa()` devuelve `None`: ninguna regla factual matchea un código de barras.
3. Termina en `handle_general_query(user_message, db_stats)` — el asesor 0.5b, que recibe en su prompt las estadísticas del negocio (`precio_promedio` entre ellas).
4. El 0.5b ve un número que no entiende y un prompt lleno de estadísticas, y contesta lo único que tiene a mano: **el promedio**.

Es exactamente el modo de falla que el SDD ya prohíbe en el requirement transversal **"Preferir preguntar antes que especular"**: un dato que el usuario escribió literal y sin ambigüedad (13 dígitos son un código de barras, no una pregunta de negocio) terminó interpretado por un modelo de 0.5b que improvisó. Un código de barras es el dato más determinístico que existe en este sistema: es una clave primaria de negocio, se resuelve con un `SELECT`, y la respuesta o existe o no existe.

Peor todavía: la respuesta es **plausible y falsa**. No dice "no entendí": afirma un número real de la base como si fuera la respuesta a lo que se preguntó.

## What Changes

- **Un código de barras se reconoce esté donde esté en el mensaje.** Si el mensaje contiene una secuencia de 6+ dígitos y el resto del mensaje no pide otra cosa, el agente SHALL resolverlo como consulta de producto: `SELECT` por barcode, respuesta exacta, sin modelo.
- **Prioridad determinística acotada, para no secuestrar otros flujos.** La detección ampliada SHALL ceder ante los flujos que legítimamente llevan un código adentro:
  - un producto pendiente de creación (el barcode es el dato que se está pidiendo) — ya tiene prioridad hoy y la conserva;
  - un mensaje con verbo de acción de gestión ("creá el producto X con codigo 779…", "borrá el 779…"): esos van a su intent, no a una consulta.
- **Un código de barras NUNCA SHALL llegar al asesor general.** Si hay un código en el mensaje y no se pudo resolver como acción, el agente responde por base de datos o pregunta. No especula.
- **Sin regresión en el escaneo pelado**: mandar solo los dígitos sigue funcionando idéntico (producto encontrado / producto no encontrado + arranca creación).

## Capabilities

### Modified Capabilities
- `ai-agent`: el reconocimiento de código de barras deja de exigir que el mensaje sean puros dígitos; un código de barras nunca se contesta con una especulación del asesor general.

## Impact

- `Backend/api/routes/controller_agent.py` — helper determinístico de detección de código de barras en el mensaje; se usa en el punto donde hoy está el `^\d{6,}$`, y como red de seguridad antes de caer al asesor general.
- **No cambia** ningún Modelfile: es un arreglo de enrutado determinístico, no de prompts. No hay que reconstruir tags con `ollama create`.
- **No cambia** el contrato del endpoint `/api/agent/chat`.
- **Mejora la latencia**: los mensajes con código de barras que hoy gastan una llamada al asesor (~9 s) pasan a resolverse por base de datos (~0.01 s).
