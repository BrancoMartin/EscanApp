## MODIFIED Requirements

### Requirement: Formulario de alta de producto
El formulario de alta de producto SHALL tener campos para código de barras, nombre, precio, descripción y proveedor, con validación de campos requeridos.

El mensaje de éxito SHALL aparecer apenas el backend confirma el alta, sin esperar a que la IA infiera categorías ni atributos.

El campo de código de barras SHALL distinguir si el código fue **tecleado a mano** o **ingresado por el lector**, con el mismo criterio que la pantalla de escaneo: si el intervalo entre caracteres supera los 50 ms, el ingreso es manual; si llega en ráfaga, es del lector. El formulario SHALL mostrar esa señal como un indicador discreto junto al campo, para que el usuario pueda verificar cuál de los dos caminos está ejercitando.

A diferencia de la pantalla de escaneo, el alta de producto NO SHALL auto-enviar el formulario cuando detecta el lector: faltan el nombre y el precio. La detección acá es informativa.

#### Scenario: Envío exitoso
- **WHEN** el usuario completa todos los campos requeridos y envía
- **THEN** se envía POST a /api/products/
- **AND** se muestra mensaje de éxito "Producto creado: {name}"

#### Scenario: Confirmación sin demora
- **WHEN** el usuario envía el formulario con datos válidos
- **THEN** el mensaje de éxito aparece apenas responde el backend (< 1 s), no varios segundos después

#### Scenario: Código de barras ingresado con el lector
- **WHEN** el usuario dispara el lector sobre el campo de código de barras
- **THEN** los caracteres llegan en ráfaga (intervalo <= 50 ms)
- **AND** el formulario indica que el código fue escaneado
- **AND** el formulario NO se envía automáticamente

#### Scenario: Código de barras tecleado a mano
- **WHEN** el usuario escribe el código de barras a mano
- **THEN** al menos un intervalo entre caracteres supera los 50 ms
- **AND** el formulario indica que el código fue ingresado a mano

#### Scenario: Reinicio de la detección
- **WHEN** el campo de código de barras queda vacío
- **THEN** la detección se reinicia y vuelve a asumir lector hasta que una pausa larga demuestre lo contrario

#### Scenario: Campos requeridos vacíos
- **WHEN** el usuario envía el formulario sin barcode, name o price
- **THEN** se muestran errores de validación en los campos faltantes

#### Scenario: Error del servidor
- **WHEN** el servidor retorna un error (ej. barcode duplicado)
- **THEN** se muestra el mensaje de error del servidor

### Requirement: Pantalla de escaneo de productos
La pantalla de escaneo SHALL permitir ingresar un código de barras, mostrar el ticket de venta pendiente, y permitir cerrar o cancelar la venta.

La pantalla SHALL distinguir el ingreso por **lector de códigos de barras** del **tecleo manual**, midiendo el intervalo entre caracteres: hasta 50 ms es el lector, más que eso es una persona escribiendo. La detección SHALL reiniciarse y volver a asumir lector cada vez que el campo queda vacío.

Cuando el código lo ingresa el lector, la pantalla SHALL auto-escanear sola al terminar la ráfaga, sin que el usuario apriete nada. Cuando el código se tecleó a mano, la pantalla NO SHALL auto-enviar: el usuario SHALL confirmar con el botón o con Enter. Esto evita disparar escaneos con códigos a medio escribir.

El cursor SHALL mantenerse en el campo de escaneo, que es el estado de trabajo normal de la pantalla.

#### Scenario: Escaneo exitoso
- **WHEN** el usuario ingresa un barcode y hace clic en "Escanear producto"
- **THEN** se agrega el producto a la venta pendiente
- **AND** se muestra el ticket actualizado

#### Scenario: Auto-escaneo con el lector
- **WHEN** el lector ingresa el código en ráfaga (intervalos <= 50 ms)
- **THEN** la pantalla dispara el escaneo sola al terminar la ráfaga
- **AND** el usuario no tiene que apretar ningún botón

#### Scenario: Sin auto-escaneo al teclear a mano
- **WHEN** el usuario escribe el código a mano (algún intervalo > 50 ms)
- **THEN** la pantalla NO dispara el escaneo automáticamente
- **AND** el escaneo ocurre recién cuando el usuario aprieta el botón o Enter

#### Scenario: Producto no encontrado
- **WHEN** el usuario escanea un barcode no registrado
- **THEN** se muestra mensaje de error

#### Scenario: Cerrar venta
- **WHEN** el usuario hace clic en "Cerrar venta"
- **THEN** la venta cambia a estado "closed"
- **AND** se muestra mensaje "Venta cerrada exitosamente"

#### Scenario: Cancelar venta completa
- **WHEN** el usuario hace clic en "Cancelar venta completa"
- **THEN** la venta se elimina

#### Scenario: Cancelar producto individual
- **WHEN** el usuario hace clic en "Cancelar producto" en un item del ticket
- **THEN** el item se elimina o decrementa su cantidad
- **AND** el ticket se actualiza
