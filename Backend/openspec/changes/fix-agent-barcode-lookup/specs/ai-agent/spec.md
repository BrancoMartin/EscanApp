## ADDED Requirements

### Requirement: Reconocimiento de código de barras en cualquier parte del mensaje

El sistema SHALL reconocer un código de barras aunque el mensaje no sea exclusivamente dígitos. Una secuencia de 6 o más dígitos consecutivos en el mensaje SHALL tratarse como código de barras, sin importar las palabras que la rodeen.

Un código de barras es el dato más determinístico del sistema: es una clave de negocio que el usuario escribe literal y que se resuelve con una consulta a la base. NUNCA SHALL interpretarlo un modelo.

La detección SHALL ceder ante los flujos que legítimamente contienen un código de barras, en este orden de prioridad:

1. **Producto pendiente de creación**: si hay una creación en curso, el código es la respuesta al paso que se está pidiendo y lo consume esa máquina de estados.
2. **Verbo de acción de gestión**: si el mensaje trae un verbo de acción (`crear`, `borrar`, `cambiar`, `asignar`, …), el mensaje es una orden y va a su intent, no a una consulta. "creá el producto X con código 7791234567890" SHALL seguir siendo una creación.
3. **Consulta por código de barras**: en cualquier otro caso, el sistema resuelve el código contra la base y responde.

#### Scenario: Código de barras pelado

- **WHEN** el usuario envía solo el código, ej. "7791234567890"
- **THEN** el sistema busca el producto por código de barras
- **AND** si existe, responde con nombre, precio, código y atributos
- **AND** si no existe, inicia el flujo de creación preguntando el nombre

#### Scenario: Código de barras acompañado de palabras

- **WHEN** el usuario envía "que producto es el 7791234567890" o "buscame el codigo 7791234567890"
- **THEN** el sistema lo resuelve como consulta de producto por código de barras
- **AND** responde con los datos del producto desde la base, sin invocar ningún modelo

#### Scenario: Código de barras inexistente acompañado de palabras

- **WHEN** el usuario pregunta por un código de barras que no está registrado
- **THEN** el sistema responde que no encontró ningún producto con ese código
- **AND** NO especula ninguna respuesta

#### Scenario: Orden de gestión con código de barras

- **WHEN** el usuario envía "creame el producto agua a 500 con codigo 7791234567890"
- **THEN** el mensaje se rutea a `crear_productos` y NO a una consulta por código de barras

#### Scenario: Creación en curso

- **WHEN** hay un producto pendiente de creación y el sistema está pidiendo el código de barras
- **THEN** el código que envía el usuario lo consume el flujo de creación
- **AND** NO se dispara una consulta por código de barras

#### Scenario: Un número corto no es un código de barras

- **WHEN** el mensaje trae un número de menos de 6 dígitos (ej. "aumentame todo un 10%")
- **THEN** el sistema NO lo interpreta como código de barras

## MODIFIED Requirements

### Requirement: Consultas generales de inventario

El sistema SHALL responder consultas generales sobre el estado del inventario: cantidad de productos, ventas del día, etc.

Un mensaje que contiene un código de barras NO SHALL llegar nunca al asesor general (`handle_general_query`). El asesor recibe en su prompt las estadísticas del negocio, y ante un número que no comprende responde con la estadística que tenga a mano —típicamente el precio promedio—, produciendo una respuesta plausible y falsa. Si el mensaje trae un código de barras, la respuesta SHALL salir de la base de datos o SHALL ser una pregunta aclaratoria.

#### Scenario: Consultar cantidad de productos

- **WHEN** el usuario pregunta "cuantos productos tengo?"
- **THEN** el sistema consulta la base de datos
- **AND** retorna el conteo total de productos

#### Scenario: Consultar ventas

- **WHEN** el usuario pregunta "cuales fueron las ventas de hoy?" o "decime las ventas que tuve este mes" o "esta semana cuantos {producto} vendi?"
- **THEN** el sistema consulta las ventas
- **AND** retorna el resumen

#### Scenario: Código de barras nunca llega al asesor general

- **WHEN** el mensaje del usuario contiene una secuencia de 6+ dígitos
- **THEN** el sistema NO invoca `handle_general_query`
- **AND** responde por base de datos o pregunta qué se quiso hacer con ese código
