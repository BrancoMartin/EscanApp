## MODIFIED Requirements

### Requirement: Performance — respuesta máxima en 3.5 segundos

El sistema SHALL completar cualquier interacción del agente IA en un máximo de **3.5 segundos** en su camino común, y NO SHALL superar **5 segundos** en el peor caso (fallbacks que requieren inferencia genuina), desde que el usuario envía el mensaje hasta que recibe la respuesta.

El hardware de referencia es una máquina **sin GPU dedicada** donde Ollama genera a ~27 tokens/s en CPU. En consecuencia, el tiempo de generación es directamente proporcional a `num_predict`: cada 27 tokens generados cuestan ~1 segundo. El presupuesto de latencia SHALL respetarse mediante tres reglas:

1. **Como máximo UN modelo por request** en el camino común de cada flujo.
2. **`num_predict` acotado** al tamaño real de la salida esperada de cada modelo.
3. **Modelos residentes** entre requests (ver "Residencia de modelos en memoria").

#### Scenario: Respuesta dentro del límite

- **WHEN** el usuario envía un mensaje al agente
- **THEN** el sistema procesa (intent detection + acción + respuesta) en menos de 3.5s

#### Scenario: Peor caso con fallback de inferencia

- **WHEN** el flujo debe recurrir a un modelo de fallback (inferencia semántica genuina)
- **THEN** la respuesta llega igualmente en menos de 5s

#### Scenario: Timeout con feedback

- **WHEN** el procesamiento supera los 3.5s
- **THEN** el frontend muestra un mensaje de que el agente está tardando más de lo esperado
- **AND** permite al usuario reintentar o cancelar

### Requirement: 9 modelos especializados de IA

El sistema SHALL definir 9 modelos Ollama especializados, cada uno con un prompt específico para una tarea concreta. Todos SHALL construirse desde `qwen2.5:0.5b`; ningún modelo del agente SHALL correr sobre un modelo base mayor, porque en el hardware de referencia (CPU, sin GPU) un modelo de 3B tarda ~27 s por llamada.

Los modelos SHALL clasificarse por su rol en la latencia:

- **Camino común** (se invocan en el flujo normal): `AttributeClassifier`, `AttributeExtractor`, `GeneralConsultant`.
- **Red de seguridad** (solo si ningún fast-path determinístico resuelve el mensaje): `CualifiquerIntent`, `IncompleteHandler`.
- **Fallback** (solo cuando la vía determinística no alcanza): `IncreaseDetector`, `CreateProduct`, `CreateCategories`.
- **Fuera de uso**: `AttributeResolver` (ver "Asignación automática de productos al agregar un atributo"). El Modelfile y el wrapper siguen en el repo; queda pendiente decidir si se eliminan.

Un request SHALL invocar como máximo UN modelo. En el hardware de referencia Ollama mantiene un solo modelo residente (RAM), así que dos modelos distintos en un mismo request se expulsan mutuamente de memoria y cada uno se recarga de disco: medido, eso llevaba `agregar_atributo` de ~3 s a ~16 s y la creación de producto a ~19 s.

#### Scenario: Modelos cargados

- **WHEN** el sistema inicia el agente
- **THEN** todos los modelos están disponibles para ser invocados según la intención detectada

#### Scenario: Modelo base correcto

- **WHEN** se reconstruye cualquier modelo del agente con `ollama create`
- **THEN** el tag resultante pesa ~397 MB (base `qwen2.5:0.5b`), no ~1.9 GB (base `qwen2.5:3b`)

### Requirement: Detección de intención (Intent Classifier)

El sistema SHALL clasificar el mensaje del usuario en uno de los siguientes intents: `ajustar_precios`, `crear_productos`, `crear_categoria`, `listar_categorias`, `agregar_atributo`, `info_incompleta`, `consulta_general`.

El intent `ajustar_precios` cubre tanto aumentos como disminuciones de precio (sinónimos: aumentar, subir, incrementar, disminuir, bajar, reducir, descontar, rebajar, poner descuento).

El controlador SHALL resolver el intent **sin invocar al clasificador Ollama** cuando el mensaje contiene un marcador inequívoco de acción (fast-path determinístico), porque esa llamada es una carga de modelo evitable:

- verbo imperativo de ajuste de precios, o verbo infinitivo + porcentaje → `ajustar_precios` (ya existente)
- verbo de listar/mostrar + "categoria(s)"/"atributo(s)" → `listar_categorias`
- verbo de creación + la palabra "categoria" → `crear_categoria`
- verbo de creación/agregado + la palabra "atributo" → `agregar_atributo`
- verbo de creación + la palabra "producto"/"articulo" → `crear_productos`

El clasificador Ollama SHALL seguir invocándose para todo mensaje que no matchee ningún fast-path, actuando como red de seguridad (incluidos los ajustes de precio expresados sin verbo imperativo, ej. "hacele un descuento del 20%").

#### Scenario: Intención de ajuste de precios (aumento)

- **WHEN** el usuario escribe "aumentame todos los productos un 15%" o "subime los precios"
- **THEN** el sistema detecta intent = "ajustar_precios"

#### Scenario: Intención de ajuste de precios (disminución)

- **WHEN** el usuario escribe "bajame la leche un 10%" o "hacele un descuento del 20% a los productos de plastico"
- **THEN** el sistema detecta intent = "ajustar_precios"

#### Scenario: Intención de crear producto

- **WHEN** el usuario describe un nuevo producto
- **THEN** el sistema detecta intent = "crear_productos"

#### Scenario: Intención de listar categorías

- **WHEN** el usuario escribe "listame las categorias" o "que categorias tengo"
- **THEN** el sistema detecta intent = "listar_categorias"

#### Scenario: Intención de consulta general

- **WHEN** el usuario pregunta "cuantos productos tengo?"
- **THEN** el sistema detecta intent = "consulta_general"

#### Scenario: Fast-path sin modelo

- **WHEN** el usuario escribe "listame las categorias" o "creame la categoria marca"
- **THEN** el controlador resuelve el intent por regex y NO invoca el clasificador Ollama

#### Scenario: Mensaje ambiguo usa el clasificador

- **WHEN** el mensaje no matchea ningún fast-path (ej. "hacele un descuento del 20% a los productos de plastico")
- **THEN** el controlador invoca el clasificador Ollama

### Requirement: Creación de producto con extracción determinística de datos

Al crear un producto vía chat (intent `crear_productos`), el controlador SHALL extraer determinísticamente del mensaje `nombre`, `precio`, `barcode` y `proveedor` cuando aparezcan explícitos, y esos valores SHALL prevalecer sobre los que devuelva el modelo `CreateProduct` (0.5b, propenso a alucinar).

El modelo `CreateProduct` SHALL invocarse **solo como fallback**: únicamente cuando la extracción determinística NO logra obtener el `nombre` del producto. Cuando el nombre se extrae del texto, el controlador NO SHALL invocar `CreateProduct` (los atributos del producto se infieren igualmente en la pasada de enriquecimiento posterior a la creación).

Reglas de extracción:
- `barcode`: primera secuencia de 6+ dígitos.
- `precio`: por marcador (`$N`, `N pesos`, `precio N`, `vale N`, `a N`) o, si no hay marcador, el primer número suelto de ≤5 dígitos que NO sea el barcode ni una cantidad (seguido de unidad: unidades/litros/kg/…).
- `nombre`: texto tras "producto/articulo", sin fillers iniciales (nuevo, un, el, llamado…) ni la parte de precio/proveedor/barcode; SHALL conservar números internos legítimos del nombre (ej. "agua 2 litros").

#### Scenario: Producto con nombre y precio explícitos

- **WHEN** el usuario escribe "creame el producto coca cola a 500"
- **THEN** el sistema toma `nombre = "coca cola"` y `precio = 500` (aunque el modelo devuelva otra cosa)
- **AND** NO invoca el modelo `CreateProduct`

#### Scenario: Número interno del nombre se conserva

- **WHEN** el usuario escribe "producto agua 2 litros a 300"
- **THEN** `nombre = "agua 2 litros"` y `precio = 300`

#### Scenario: Cantidad no se confunde con precio

- **WHEN** el usuario escribe "creame un producto lapiz 12 unidades"
- **THEN** el sistema NO toma 12 como precio (es cantidad) y solicita el precio

#### Scenario: Fallback al modelo sin nombre extraíble

- **WHEN** la extracción determinística no logra obtener el nombre del producto
- **THEN** el controlador invoca `CreateProduct` como fallback

### Requirement: Extracción de atributos por IA

El sistema SHALL extraer atributos (categoría + valor) del nombre y descripción de un producto usando el modelo `AttributeExtractor`, en **una única llamada a modelo** por creación de producto.

Las categorías faltantes que aparezcan en la salida de `AttributeExtractor` SHALL crearse determinísticamente en la BD. El modelo `CreateCategories` SHALL invocarse **solo como fallback**, cuando `AttributeExtractor` no devuelve ningún atributo.

#### Scenario: Extracción al crear producto

- **WHEN** se crea un producto desde el chat
- **THEN** el sistema invoca `AttributeExtractor` para inferir atributos
- **AND** crea determinísticamente las categorías y atributos faltantes que aparezcan en su salida
- **AND** asocia los atributos al producto

#### Scenario: Proveedor informado al crear producto

- **WHEN** se crea un producto con el campo proveedor informado
- **THEN** el sistema garantiza **determinísticamente** (sin invocar ningún modelo) que exista la categoría `proveedor`
- **AND** el sistema invoca `AttributeExtractor` con la categoría `proveedor` disponible
- **AND** `AttributeExtractor` SHALL devolver un atributo con `categoria = "proveedor"` y `valor` igual al proveedor ingresado por el usuario
- **AND** si el modelo omite ese atributo, el wrapper del agente SHALL agregarlo de forma determinística
- **AND** el sistema asocia ese atributo al producto mediante ProductAttribute

#### Scenario: Proveedor vacío al crear producto

- **WHEN** se crea un producto sin proveedor o con proveedor vacío, null, None, n/a, desconocido o similar
- **THEN** NO SHALL crearse la categoría `proveedor`
- **AND** `AttributeExtractor` SHALL NOT devolver atributos de categoría `proveedor`

#### Scenario: Fallback de categorías

- **WHEN** `AttributeExtractor` no devuelve ningún atributo para el producto
- **THEN** el sistema invoca `CreateCategories` como fallback para bootstrapear categorías

### Requirement: Asignación automática de productos al agregar un atributo

Al agregar un atributo vía chat, **la aplicación SHALL decidir sola** a qué productos corresponde el atributo. NO SHALL preguntarle al usuario a qué producto asignarlo: esa no es una decisión que el comerciante deba tomar.

La asignación SHALL resolverse **determinísticamente contra la base de datos**, comparando el valor del atributo con el `nombre` y la `descripcion` de cada producto **sin acentos y por raíz** (así "galletas" encuentra "Galleta rellena", y "plastico" encuentra "plástico"). Todas las raíces del valor deben aparecer en el producto, para que "galletas de chocolate" no matchee cualquier producto con "chocolate".

Al crear un producto, el sistema SHALL vincularlo determinísticamente a los atributos que YA existen y aparecen en su nombre o descripción. Así, un atributo creado cuando todavía no había productos se aplica solo a los que se creen después.

Si ningún producto menciona el atributo, el sistema SHALL crear el atributo sin asignarlo e informarlo, sin preguntar nada.

`AttributeResolver` NO SHALL invocarse. Se evaluó para el caso semántico y es peor que inútil en 0.5b: con productos `[Leche entera, Yogur bebible, Martillo]` y el atributo "lacteos" devolvió `[Leche entera, Martillo]`; con "golosinas" sobre `[gomitas, turron, Pipas]` devolvió los tres. Asignaría atributos equivocados **en silencio**, que es exactamente el tipo de decisión que no puede quedar sin revisar. El Modelfile y su wrapper permanecen en el repositorio pero no se usan.

#### Scenario: Coincidencia — la app asigna sola

- **WHEN** el usuario agrega el atributo "gomitas" y existe un producto llamado "gomitas"
- **THEN** el sistema se lo asigna automáticamente y lo informa, sin preguntar nada

#### Scenario: Categoría explícita — cero modelos

- **WHEN** el usuario escribe "agregar atributo ropa de categoria indumentaria"
- **THEN** el sistema resuelve categoría y valor por regex y asigna contra la BD, sin invocar ningún modelo

#### Scenario: Sin productos que lo mencionen

- **WHEN** ningún producto menciona el valor del atributo
- **THEN** el sistema crea el atributo, informa que todavía no hay productos que lo lleven, y NO pregunta nada
- **AND** NO invoca ningún modelo para adivinar a qué producto asignarlo

#### Scenario: Producto nuevo toma los atributos existentes

- **WHEN** existe el atributo "galletas" y el usuario crea el producto "Galletas de agua"
- **THEN** el sistema le asigna el atributo "galletas" automáticamente, sin modelo

### Requirement: Resiliencia ante salidas truncadas del modelo

Los wrappers SHALL tolerar que la respuesta del modelo venga cortada por `num_predict` (JSON truncado). Descartar la respuesta completa NO es gratis: dispara el fallback a otro modelo y duplica la latencia del request (medido: 19 s en la creación de producto).

`AttributeExtractor` SHALL rescatar los objetos `{"categoria","valor"}` que quedaron completos en un JSON truncado, y SHALL acotar a 3 la cantidad de atributos aceptados (el 0.5b tiende a emitir uno por cada categoría existente, inventando valores). La lista de categorías enviada al modelo SHALL estar acotada por el mismo motivo.

#### Scenario: JSON truncado

- **WHEN** el modelo corta su salida a mitad de un JSON
- **THEN** el wrapper rescata los atributos completos y NO invoca un segundo modelo

#### Scenario: Modelo inventa un atributo por categoría

- **WHEN** el modelo devuelve más de 3 atributos
- **THEN** el sistema conserva los primeros 3 y descarta el resto

### Requirement: Consultas generales de inventario

El sistema SHALL responder consultas generales sobre el estado del inventario: cantidad de productos, precios, ventas del día/semana/mes.

Las preguntas **factuales** (las que la base de datos puede contestar con exactitud) SHALL responderse **calculando el dato en la BD, sin invocar ningún modelo**: cantidad de productos, producto más caro/más barato, precio promedio, y ventas de hoy / últimos 7 días / últimos 30 días.

Un modelo de 0.5b NO es confiable para reportar números: copiaba las cifras de los ejemplos del prompt (respondió "3 ventas por $6000" con UNA sola venta en la base) y llegó a decir que el producto más caro era `material`, que es una CATEGORÍA. Por eso el prompt del asesor NO SHALL contener números de ejemplo.

`GeneralConsultant` SHALL invocarse solo para las preguntas abiertas que la BD no sabe calcular. Los datos que recibe SHALL calcularse en la BD e incluir, según la pregunta: productos con precio, ventas por período y unidades vendidas.

#### Scenario: Consultar cantidad de productos

- **WHEN** el usuario pregunta "cuantos productos tengo?"
- **THEN** el sistema responde el conteo exacto desde la BD, sin invocar ningún modelo

#### Scenario: Consultar producto más caro

- **WHEN** el usuario pregunta "cual es mi producto mas caro?"
- **THEN** el sistema responde el nombre y precio reales del producto (nunca una categoría)

#### Scenario: Consultar ventas

- **WHEN** el usuario pregunta "cuales fueron las ventas de hoy?" o "cuanto vendi esta semana?"
- **THEN** el sistema responde la cantidad de ventas y el total facturado reales del período
- **AND** si no hubo ventas, lo dice explícitamente

#### Scenario: Pregunta abierta

- **WHEN** el usuario hace una pregunta que la BD no sabe calcular (ej. "que me conviene hacer para vender mas?")
- **THEN** el sistema invoca `GeneralConsultant` con los datos calculados

## ADDED Requirements

### Requirement: Un porcentaje que el usuario no escribió NUNCA se aplica

El sistema NO SHALL ejecutar un ajuste de precios con un porcentaje que no provenga del mensaje del usuario. Si el mensaje **no contiene ningún dígito**, no hay porcentaje posible, y cualquier valor devuelto por `IncreaseDetector` SHALL descartarse: el sistema SHALL pedir el porcentaje.

Motivo (bug encontrado y corregido): ante la pregunta **"me conviene subir los precios?"** el clasificador la enrutaba a `ajustar_precios`, `IncreaseDetector` (0.5b) inventaba `porcentaje: 100`, y el sistema **aumentaba el precio de TODOS los productos al doble**. Una pregunta destruía los datos del comercio.

Adicionalmente, una **pregunta de opinión sobre precios** (termina en `?` o abre con "me conviene", "debería", "conviene", "vale la pena"…) y sin dígitos SHALL tratarse como `consulta_general`, NO como una orden de ajuste.

#### Scenario: Pregunta de opinión no modifica precios

- **WHEN** el usuario pregunta "me conviene subir los precios?" o "deberia bajar los precios?"
- **THEN** el sistema responde como consulta y NO modifica ningún precio

#### Scenario: Orden sin porcentaje pide el porcentaje

- **WHEN** el usuario escribe "subime los precios" (orden, sin porcentaje)
- **THEN** el sistema pide el porcentaje y NO modifica ningún precio

#### Scenario: Orden con porcentaje se ejecuta

- **WHEN** el usuario escribe "aumentame todos los productos un 10%"
- **THEN** el sistema aplica el 10% (el fast-path determinístico sigue funcionando)

### Requirement: Residencia de modelos en memoria (keep_alive)

Los modelos SHALL permanecer cargados en memoria entre requests. El cliente SHALL enviar `keep_alive` en cada invocación (valor por defecto: 30 minutos), porque el servidor Ollama de la máquina de ejecución tiene `OLLAMA_KEEP_ALIVE=0` como default (descarga inmediata) y el `keep_alive` del request lo sobrescribe.

El código NO SHALL leer la variable de entorno `OLLAMA_KEEP_ALIVE` para poblar ese valor, porque toma el `0` del servidor y reintroduce la descarga inmediata. SHALL usarse una variable propia (`AGENT_KEEP_ALIVE`).

El backend SHALL precargar el modelo de intent en segundo plano al arrancar, para que el primer mensaje del usuario no pague la carga del modelo.

#### Scenario: Modelo residente entre requests

- **WHEN** el usuario envía dos mensajes seguidos que usan el mismo modelo
- **THEN** el segundo NO paga el tiempo de carga del modelo (~2.2s)

#### Scenario: Env del sistema no degrada la latencia

- **WHEN** la máquina tiene `OLLAMA_KEEP_ALIVE=0` en el entorno
- **THEN** el agente igualmente mantiene sus modelos residentes (envía su propio `keep_alive` por request)

#### Scenario: Precarga al arrancar

- **WHEN** el backend termina de levantar
- **THEN** el modelo de intent ya está cargado en memoria
