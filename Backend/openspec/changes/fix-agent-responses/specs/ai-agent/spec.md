## MODIFIED Requirements

### Requirement: Detección de intención (Intent Classifier)

El sistema SHALL clasificar el mensaje del usuario en uno de los siguientes intents: `ajustar_precios`, `crear_productos`, `crear_categoria`, `listar_categorias`, `agregar_atributo`, `info_incompleta`, `consulta_general`.

El intent `ajustar_precios` cubre tanto aumentos como disminuciones de precio (sinónimos: aumentar, subir, incrementar, disminuir, bajar, reducir, descontar, rebajar, poner descuento).

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

### Requirement: Creación de productos vía chat

El sistema SHALL guiar al usuario en la creación de un producto mediante un flujo conversacional paso a paso con este orden: **nombre → precio → descripción (opcional) → proveedor (opcional) → código de barras**. La descripción y el proveedor SHALL preguntarse SIEMPRE una vez (no se infieren en silencio), y el usuario SHALL poder omitirlos respondiendo "no" (u otra negación). Los datos que el usuario ya proporcionó explícitamente en el mensaje inicial NO SHALL volver a preguntarse.

#### Scenario: Flujo completo de creación

- **WHEN** el usuario indica querer crear un producto
- **THEN** el sistema solicita el nombre
- **AND** luego solicita el precio
- **AND** luego pregunta si desea agregar una descripción (que puede omitir con "no")
- **AND** luego pregunta si tiene proveedor (que puede omitir con "no")
- **AND** luego solicita el código de barras
- **AND** finalmente crea el producto con la descripción/proveedor indicados y los atributos inferidos

#### Scenario: Descripción y proveedor omitidos

- **WHEN** el usuario responde "no" a la pregunta de descripción y a la de proveedor
- **THEN** el producto se crea con descripción y proveedor vacíos (sin inventar valores)

#### Scenario: Proveedor ya indicado en el mensaje inicial

- **WHEN** el usuario escribe "creame el producto X a 500 proveedor Distribuidora Norte"
- **THEN** el sistema NO vuelve a preguntar el proveedor (usa "Distribuidora Norte") y solo pregunta lo que falte

#### Scenario: Escaneo de barcode de producto no existente

- **WHEN** el usuario escanea un barcode no registrado
- **THEN** el sistema inicia el flujo de creación preguntando el nombre
- **AND** guarda el barcode como pendiente

#### Scenario: Producto duplicado por barcode

- **WHEN** el usuario completa la creación con un barcode ya existente
- **THEN** el sistema rechaza con mensaje "Ya existe un producto con ese codigo de barras"

## ADDED Requirements

### Requirement: Preferir preguntar antes que especular

Ante cualquier solicitud que el sistema no pueda interpretar con confianza a partir de lo que el usuario escribió literalmente, el sistema SHALL formular una pregunta aclaratoria en lugar de ejecutar una acción basada en inferencias de un modelo (que puede alucinar). Los datos que el usuario expresa explícitamente (valores, nombres, porcentajes, productos, atributos) SHALL extraerse determinísticamente y tienen prioridad sobre cualquier salida de modelo. Los modelos SHALL usarse solo para lo que requiere inferencia genuina (clasificación de intención, inferencia de categoría, redacción de respuestas), y su salida NO SHALL provocar la creación o modificación de datos que el usuario no pidió explícitamente.

#### Scenario: Interpretación incierta

- **WHEN** el sistema no puede determinar con confianza qué acción o datos pidió el usuario
- **THEN** pregunta en vez de ejecutar una acción especulada

#### Scenario: Dato explícito prevalece sobre el modelo

- **WHEN** el usuario escribe un dato de forma explícita (ej. "atributo galletas")
- **THEN** el sistema usa ese dato literal y NO un valor inferido o alucinado por un modelo

### Requirement: Ajuste de precios por tipo y operación

El sistema SHALL soportar el ajuste de precios con dos operaciones (`aumento`, `disminucion`) sobre cuatro tipos de destino (`todos`, `individual`, `por_atributo`, `por_categoria`). El modelo `IncreaseDetector` SHALL devolver `tipo`, `porcentaje`, `operacion` y `value`.

La fórmula aplicada SHALL ser:
- operación `aumento`: `precio = precio * (1 + porcentaje / 100)`
- operación `disminucion`: `precio = precio * (1 - porcentaje / 100)`

El mensaje de respuesta SHALL usar el verbo correcto según la operación ("aumentó" o "disminuyó").

#### Scenario: Aumentar todos los productos

- **WHEN** el usuario pide aumentar todos los productos un porcentaje
- **THEN** el sistema aplica `precio * (1 + porcentaje / 100)` a todos los productos
- **AND** retorna el conteo de productos actualizados y el mensaje indica "aumentó"

#### Scenario: Disminuir todos los productos

- **WHEN** el usuario pide "bajame todos los productos un 10%"
- **THEN** el sistema aplica `precio * (1 - porcentaje / 100)` a todos los productos
- **AND** el mensaje indica "disminuyó"

#### Scenario: Ajustar producto individual

- **WHEN** el usuario pide ajustar un producto específico por nombre
- **THEN** el sistema busca el producto por nombre con ILIKE
- **AND** aplica el ajuste (según operación) solo a ese producto

#### Scenario: Ajustar por atributo

- **WHEN** el usuario pide ajustar productos con un atributo específico (ej. "aumentame los productos de mugol", "bajame los productos de plastico")
- **THEN** el sistema busca el atributo en la base de datos
- **AND** aplica el ajuste solo a productos que tengan ese atributo

#### Scenario: Ajustar por proveedor

- **WHEN** el usuario pide "aumentame los productos de mi proveedor Distribuidora Norte"
- **THEN** el sistema resuelve el valor del atributo de categoría `proveedor`
- **AND** aplica el ajuste a los productos vinculados a ese proveedor

#### Scenario: Ajustar por categoría explícita

- **WHEN** el usuario menciona la palabra "categoria" (ej. "aumentame los productos de la categoria material un 10%")
- **THEN** el sistema busca la categoría por nombre con ILIKE
- **AND** aplica el ajuste a todos los productos con atributos de esa categoría

#### Scenario: Falta el porcentaje

- **WHEN** el usuario pide un ajuste sin indicar el porcentaje
- **THEN** el sistema solicita el porcentaje de ajuste

### Requirement: Flujo detallado de ajuste por atributo con descubrimiento automático

Cuando el usuario pide ajustar precios por un atributo que no existe en la BD, el sistema SHALL usar múltiples agentes para descubrir la categoría, crearla, crear el atributo, y auto-asignar productos, aplicando la operación (aumento o disminución) indicada.

#### Scenario: Atributo existe directamente

- **WHEN** el usuario pide ajustar por un atributo que ya existe en la BD
- **THEN** el sistema busca productos vinculados a ese atributo vía ProductAttribute
- **AND** aplica el ajuste a esos productos

#### Scenario: Atributo no existe — detectar categoría con agente

- **WHEN** el usuario pide ajustar por un atributo que NO existe en la BD
- **THEN** el sistema invoca el modelo detect_category_and_value para inferir a qué categoría pertenece
- **AND** si la categoría inferida no existe, la crea en la BD

#### Scenario: Atributo no existe sin categoría inferible

- **WHEN** el agente no puede inferir la categoría del atributo
- **THEN** el sistema busca un fallback por ILIKE en nombres de categorías existentes
- **AND** si encuentra una categoría similar, busca productos con atributos de esa categoría y aplica el ajuste

#### Scenario: Atributo creado — auto-asignar productos existentes

- **WHEN** se crea un nuevo atributo
- **THEN** el sistema busca productos cuyo nombre o descripción contengan el valor del atributo
- **AND** asigna automáticamente el atributo a esos productos vía ProductAttribute
- **AND** aplica el ajuste de precio a esos productos

#### Scenario: Atributo creado — sin productos detectados

- **WHEN** se crea un nuevo atributo pero no se encuentran productos automáticamente
- **THEN** el sistema retorna mensaje indicando que no encontró productos para asignar
- **AND** guarda el contexto para que el usuario pueda especificar manualmente qué productos vincular

### Requirement: Wiring del intent de precios en el controlador

El controlador `controller_agent.py` SHALL mapear el intent `ajustar_precios` devuelto por el clasificador y ejecutar la acción de ajuste. El controlador SHALL leer el campo `operacion` de `IncreaseDetector` y aplicar aumento o disminución en consecuencia. Por compatibilidad, el controlador MAY aceptar también el nombre histórico `aumentar_precios` como alias de `ajustar_precios`.

#### Scenario: Intent de ajuste enrutado correctamente

- **WHEN** el clasificador devuelve `intent = "ajustar_precios"`
- **THEN** el controlador entra en la rama de ajuste de precios (no en consulta general)

#### Scenario: Operación respetada

- **WHEN** `IncreaseDetector` devuelve `operacion = "disminucion"`
- **THEN** el controlador aplica `precio * (1 - porcentaje / 100)`
- **AND** el mensaje de respuesta usa el verbo "disminuyó"

### Requirement: Robustez determinística del ajuste de precios ante modelos poco fiables

Dado que los modelos Ollama de 0.5b (clasificador de intención e `IncreaseDetector`) pueden equivocarse, el controlador SHALL aplicar garantías determinísticas que NO dependan de esos modelos:

- Si el mensaje contiene un verbo imperativo de ajuste (aumentame, bajame, subime, descontame, etc.), el controlador SHALL forzar `intent = ajustar_precios` aunque el clasificador devuelva otro intent (salvo que ya sea una acción de creación de producto/categoría/atributo).
- Si el mensaje contiene un verbo infinitivo de ajuste (aumentar, bajar, etc.) junto a un porcentaje explícito, también SHALL forzar `ajustar_precios`.
- Si `IncreaseDetector` no devuelve porcentaje pero el mensaje contiene "N%" o "N por ciento", el controlador SHALL extraer el porcentaje por regex.
- La operación (aumento/disminución) SHALL derivarse del verbo del mensaje cuando sea inequívoco, por encima de lo que devuelva el modelo.
- Si no se devuelve `tipo` pero hay un objetivo (atributo o producto), el controlador SHALL asumir `por_atributo`.
- El fallback de información incompleta NO SHALL dispararse cuando el mensaje contiene un porcentaje explícito.

#### Scenario: Clasificador falla en un ajuste completo

- **WHEN** el usuario escribe "aumentame las gomitas un 30%" pero el clasificador lo etiqueta como `consulta_general`
- **THEN** el controlador fuerza `ajustar_precios`, extrae porcentaje=30 y operación=aumento por regex
- **AND** aumenta el precio de "gomitas" un 30% (nunca responde `info_incompleta`)

#### Scenario: Consulta genuina con verbo en pasado no se fuerza

- **WHEN** el usuario pregunta "cuánto aumentaron las ventas este mes" (sin verbo imperativo ni porcentaje)
- **THEN** el controlador NO fuerza `ajustar_precios`
- **AND** el mensaje se responde como `consulta_general`

### Requirement: Agregado de atributo con extracción determinística del valor

Al agregar un atributo vía chat (intent `agregar_atributo`), el VALOR del atributo SHALL extraerse determinísticamente del mensaje (el texto que sigue a la palabra "atributo"), y NO SHALL inferirse con un modelo, porque los modelos de 0.5b alucinan el valor (ej. devolvían `categoria=marca, valor=material` para "creame el atributo galletas").

- El controlador SHALL soportar categoría explícita: "... de categoria X" o "... de/en <categoría existente>"; en "... de categoria X" la palabra "categoria" SHALL removerse del nombre.
- Un "de <palabra>" que no sea una categoría existente ni lleve la palabra "categoria" NO SHALL partir el valor (ej. "galletas de chocolate" es un único valor).
- Si no hay categoría explícita, la categoría SHALL inferirse con `AttributeClassifier`; si la inferencia falla, el default SHALL ser la categoría genérica `tipo`.
- El controlador NO SHALL usar ningún modelo para inferir el VALOR del atributo. Si no puede extraerlo determinísticamente del texto, SHALL PREGUNTAR (no especular).

#### Scenario: Crear atributo con valor explícito

- **WHEN** el usuario escribe "creame el atributo galletas"
- **THEN** el sistema crea un atributo con `valor = "galletas"` (nunca "material" ni "marca")
- **AND** la categoría se infiere o queda como `tipo` si no puede inferirse

#### Scenario: Crear atributo con categoría explícita

- **WHEN** el usuario escribe "agregar atributo ropa de categoria indumentaria"
- **THEN** el sistema crea el atributo `valor = "ropa"` en la categoría `indumentaria`

#### Scenario: Valor con "de" que no es categoría

- **WHEN** el usuario escribe "creame el atributo galletas de chocolate" y "chocolate" no es una categoría existente
- **THEN** el sistema toma `valor = "galletas de chocolate"` como un único valor

### Requirement: Asignación manual de producto a atributo

El sistema SHALL soportar asignar explícitamente un producto existente a un atributo mediante frases como "asigna el producto X al atributo Y" o "asigna el producto X a la categoria Y" (en cualquier orden). El "target" (Y) puede escribirse como `atributo` o como `categoria` porque el usuario a veces los confunde; el sistema lo resuelve. Esta acción SHALL detectarse determinísticamente ANTES de clasificar el intent (sin depender del clasificador ni de ningún modelo), exigiendo la palabra "producto", un target (`atributo` o `categoria`) y un verbo de asignación (asignar, vincular, relacionar, poner, etc.).

- El producto SHALL buscarse por nombre con ILIKE; si no existe, el sistema SHALL responder que no lo encontró (con pregunta) y NO SHALL crear nada.
- El target SHALL resolverse así, SIN especular:
  - Si coincide con un **atributo** existente (ILIKE) → se asigna el producto a ese atributo.
  - Si coincide con una **categoría** existente con **un solo** atributo → se asigna a ese atributo.
  - Si coincide con una **categoría** con **0 o varios** atributos → el sistema SHALL PREGUNTAR a qué atributo asignar (listando los disponibles si los hay).
  - Si NO coincide con ningún atributo ni categoría → el sistema SHALL PREGUNTAR si crear el atributo, en lugar de inventarlo.
- El sistema SHALL crear el vínculo `ProductAttribute` y NO SHALL duplicarlo si ya existe.
- `action_executed` SHALL ser `asignar_atributo`.

#### Scenario: Asignar producto a atributo existente

- **WHEN** el usuario escribe "asigname el producto pepito al atributo galletas" y ambos existen
- **THEN** el sistema vincula "pepito" al atributo "galletas" y responde "Se asigno el atributo 'galletas' al producto 'pepito'."

#### Scenario: Target expresado como "categoria" pero es un atributo

- **WHEN** el usuario escribe "asigname el producto pepito a la categoria galletas" y "galletas" existe como atributo
- **THEN** el sistema resuelve "galletas" como atributo y realiza la misma asignación (no crea "Pepperoni" ni nada especulado)

#### Scenario: Target es una categoría con varios atributos

- **WHEN** el usuario pide asignar un producto a una categoría que tiene varios atributos
- **THEN** el sistema PREGUNTA a cuál de esos atributos asignar

#### Scenario: Target inexistente

- **WHEN** el usuario pide asignar a un atributo/categoría que no existe
- **THEN** el sistema PREGUNTA si debe crear ese atributo, sin crearlo automáticamente

#### Scenario: Producto inexistente

- **WHEN** el usuario pide asignar un producto que no existe
- **THEN** el sistema responde que no encontró ese producto y no crea ningún vínculo

### Requirement: Creación de producto con extracción determinística de datos

Al crear un producto vía chat (intent `crear_productos`), el controlador SHALL extraer determinísticamente del mensaje `nombre`, `precio`, `barcode` y `proveedor` cuando aparezcan explícitos, y esos valores SHALL prevalecer sobre los que devuelva el modelo `CreateProduct` (0.5b, propenso a alucinar).

Reglas de extracción:
- `barcode`: primera secuencia de 6+ dígitos.
- `precio`: por marcador (`$N`, `N pesos`, `precio N`, `vale N`, `a N`) o, si no hay marcador, el primer número suelto de ≤5 dígitos que NO sea el barcode ni una cantidad (seguido de unidad: unidades/litros/kg/…).
- `nombre`: texto tras "producto/articulo", sin fillers iniciales (nuevo, un, el, llamado…) ni la parte de precio/proveedor/barcode; SHALL conservar números internos legítimos del nombre (ej. "agua 2 litros").

#### Scenario: Producto con nombre y precio explícitos

- **WHEN** el usuario escribe "creame el producto coca cola a 500"
- **THEN** el sistema toma `nombre = "coca cola"` y `precio = 500` (aunque el modelo devuelva otra cosa)

#### Scenario: Número interno del nombre se conserva

- **WHEN** el usuario escribe "producto agua 2 litros a 300"
- **THEN** `nombre = "agua 2 litros"` y `precio = 300`

#### Scenario: Cantidad no se confunde con precio

- **WHEN** el usuario escribe "creame un producto lapiz 12 unidades"
- **THEN** el sistema NO toma 12 como precio (es cantidad) y solicita el precio

### Requirement: Creación de categoría con extracción determinística del nombre

Al crear una categoría vía chat (intent `crear_categoria`), el nombre SHALL extraerse determinísticamente del mensaje —de "categoria X" o de "agrupar/clasificar por X"— removiendo fillers (llamada, nueva, de, artículos) y cláusulas finales (para/que/con). NO SHALL depender de un modelo.

#### Scenario: Nombre con filler

- **WHEN** el usuario escribe "creame la categoria llamada proveedores"
- **THEN** el sistema crea la categoría `proveedores`

#### Scenario: Agrupar por criterio

- **WHEN** el usuario escribe "quiero agrupar los productos por marca"
- **THEN** el sistema crea la categoría `marca`

### Requirement: Fallback de información incompleta en acciones ambiguas

El manejo de campos faltantes en flujos concretos (porcentaje de ajuste, nombre, precio y código de barras al crear producto) SHALL seguir siendo determinístico e inline, sin invocar ningún modelo, para preservar la latencia (< 3.5s) y la confiabilidad.

Adicionalmente, cuando un mensaje sea clasificado como `consulta_general` pero contenga un verbo de acción de gestión (crear, aumentar, bajar, agregar, borrar, etc.) — es decir, el usuario intenta hacer algo pero la solicitud está incompleta o es ambigua —, el sistema SHALL invocar el modelo `IncompleteHandler` (`handle_incomplete_info`) para devolver UNA pregunta aclaratoria puntual, en lugar de una respuesta genérica del asesor general.

La detección de "acción ambigua" SHALL ser una heurística determinística en el controlador (lista blanca de verbos de acción), NO una nueva clasificación por modelo, para no alterar los flujos que ya funcionan.

#### Scenario: Acción incompleta cae en consulta general

- **WHEN** el usuario escribe "quiero aumentar algunos productos" (verbo de acción, sin porcentaje ni objetivo claro) y el clasificador devuelve `consulta_general`
- **THEN** el controlador detecta un verbo de acción en el mensaje
- **AND** invoca `IncompleteHandler` y responde con una pregunta aclaratoria (`action_executed = "info_incompleta"`)

#### Scenario: Consulta genuina no se ve afectada

- **WHEN** el usuario pregunta "cuantos productos tengo?" (sin verbos de acción de gestión)
- **THEN** el controlador NO invoca `IncompleteHandler`
- **AND** responde con el asesor general (`consulta_general`)

#### Scenario: Campo faltante en flujo concreto sigue inline

- **WHEN** al usuario le falta el porcentaje en un ajuste de precios o un dato al crear un producto
- **THEN** el sistema pregunta el dato faltante de forma inline y determinística, sin invocar `IncompleteHandler`

## REMOVED Requirements

### Requirement: Aumento de precios por tipo

**Reason**: Reemplazado por "Ajuste de precios por tipo y operación", que generaliza a aumento + disminución y agrega el tipo `por_categoria`.

**Migration**: El comportamiento de aumento se conserva íntegro como la operación `aumento`; se agrega la operación `disminucion`.

### Requirement: Flujo detallado de aumento por atributo con descubrimiento automático

**Reason**: Reemplazado por "Flujo detallado de ajuste por atributo con descubrimiento automático", idéntico salvo que aplica la operación (aumento o disminución) indicada por el usuario.

**Migration**: Ninguna migración de datos; solo se generaliza el verbo de la operación.
