# UI Domain

## Requirements

### Requirement: Navegación general
El sistema SHALL mostrar una barra de navegación superior con enlaces a Inicio, Agregar producto, Escanear productos e Historial de ventas.

#### Scenario: Navegación visible en todas las páginas
- **WHEN** el usuario navega a cualquier página
- **THEN** la barra de navegación está presente con los 4 enlaces

#### Scenario: Navegación a Inicio
- **WHEN** el usuario hace clic en "Inicio"
- **THEN** redirige a /

#### Scenario: Navegación a Agregar producto
- **WHEN** el usuario hace clic en "Agregar producto"
- **THEN** redirige a /add-product

#### Scenario: Navegación a Escanear productos
- **WHEN** el usuario hace clic en "Escanear productos"
- **THEN** redirige a /scan-products

#### Scenario: Navegación a Historial de ventas
- **WHEN** el usuario hace clic en "Historial de ventas"
- **THEN** redirige a /sales-history

### Requirement: Página de inicio
La página de inicio SHALL mostrar el título "EscanApp" y tres botones principales: Agregar Producto, Historial de Ventas, Escanear Productos.

#### Scenario: Botones de acción visibles
- **WHEN** el usuario carga la página de inicio
- **THEN** ve tres botones con las acciones principales
- **AND** un botón flotante para el chat del agente IA

### Requirement: Formulario de alta de producto
El formulario de alta de producto SHALL tener campos para código de barras, nombre, precio, descripción y proveedor, con validación de campos requeridos.

#### Scenario: Envío exitoso
- **WHEN** el usuario completa todos los campos requeridos y envía
- **THEN** se envía POST a /api/products/
- **AND** se muestra mensaje de éxito "Producto creado: {name}"

#### Scenario: Campos requeridos vacíos
- **WHEN** el usuario envía el formulario sin barcode, name o price
- **THEN** se muestran errores de validación en los campos faltantes

#### Scenario: Error del servidor
- **WHEN** el servidor retorna un error (ej. barcode duplicado)
- **THEN** se muestra el mensaje de error del servidor

### Requirement: Pantalla de escaneo de productos
La pantalla de escaneo SHALL permitir ingresar un código de barras, mostrar el ticket de venta pendiente, y permitir cerrar o cancelar la venta.

#### Scenario: Escaneo exitoso
- **WHEN** el usuario ingresa un barcode y hace clic en "Escanear producto"
- **THEN** se agrega el producto a la venta pendiente
- **AND** se muestra el ticket actualizado

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

### Requirement: Historial de ventas con calendario
La pantalla de historial SHALL mostrar un calendario para seleccionar una fecha y listar las ventas de ese día.

#### Scenario: Seleccionar fecha
- **WHEN** el usuario selecciona una fecha en el calendario
- **THEN** se cargan las ventas de esa fecha

#### Scenario: Ver detalle de venta
- **WHEN** el usuario hace clic en una venta de la lista
- **THEN** se abre un modal con el detalle de la venta (productos, cantidades, subtotales)

#### Scenario: Fecha sin ventas
- **WHEN** el usuario selecciona una fecha sin ventas
- **THEN** se muestra indicador de que no hay ventas

### Requirement: Panel de chat con agente IA
El sistema SHALL mostrar un panel lateral de chat con el agente IA, accesible desde el botón flotante en la página de inicio.

#### Scenario: Abrir chat
- **WHEN** el usuario hace clic en el botón flotante 🤖
- **THEN** se abre el panel lateral del agente

#### Scenario: Cerrar chat
- **WHEN** el usuario hace clic en ✕
- **THEN** se cierra el panel

#### Scenario: Enviar mensaje
- **WHEN** el usuario escribe un mensaje y presiona Enter o hace clic en "Enviar"
- **THEN** se envía POST a /api/agent/chat
- **AND** se muestra la respuesta del agente

#### Scenario: Mensaje de bienvenida con ejemplos
- **WHEN** el chat se abre por primera vez
- **THEN** el agente muestra un mensaje de bienvenida con ejemplos de comandos basados en productos y categorías existentes

#### Scenario: Historial persistente
- **WHEN** el usuario cierra y vuelve a abrir el chat
- **THEN** el historial de conversación se recupera de localStorage

#### Scenario: Animación de carga mientras espera
- **WHEN** el agente está procesando un mensaje
- **THEN** se muestra una animación de carga visible (tres puntos animados)
- **AND** el botón de envío se deshabilita mostrando "..."

#### Scenario: Detección automática de barcode
- **WHEN** el usuario escanea un código de barras (6+ dígitos a alta velocidad)
- **THEN** el input muestra un indicador verde "📷 Barcode detectado"

### Requirement: Diseño responsive
La interfaz SHALL adaptarse a diferentes tamaños de pantalla, con media queries para tablet y móvil.

#### Scenario: Tablet (max-width 768px)
- **WHEN** la pantalla es menor a 768px
- **THEN** los formularios usan layout de una columna
- **AND** el panel de chat ocupa todo el ancho

#### Scenario: Móvil (max-width 480px)
- **WHEN** la pantalla es menor a 480px
- **THEN** los textos y espaciados se reducen proporcionalmente

### Requirement: Tema visual consistente
El sistema SHALL usar un tema visual consistente con paleta púrpura (#7b46ff como primario), fondos claros (#f6f4ff), bordes redondeados y sombras suaves.

#### Scenario: Paleta de colores aplicada
- **WHEN** se cargan los estilos
- **THEN** los botones usan gradient púrpura (#7b46ff → #b565ff)
- **AND** los inputs tienen borde primario con box-shadow en focus
