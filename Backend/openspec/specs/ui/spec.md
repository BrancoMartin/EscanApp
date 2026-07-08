# UI Domain

## Purpose

Define la interfaz web (React 19 + Vite) del sistema: navegación, página de inicio, formularios de alta de producto, pantalla de escaneo, historiales de ventas y el panel de chat con el agente IA. Establece el tema visual consistente (paleta púrpura `#7b46ff`, fondo `#f6f4ff`, bordes redondeados y sombras suaves) y el comportamiento responsive.

## Requirements

### Requirement: Navegación general
El sistema SHALL mostrar una barra de navegación superior con enlaces a Inicio, Agregar producto, Escanear productos, Historial de ventas y Ventas de las últimas 24 hs.

#### Scenario: Navegación visible en todas las páginas
- **WHEN** el usuario navega a cualquier página
- **THEN** la barra de navegación está presente con los 5 enlaces

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

#### Scenario: Navegación a Ventas de las últimas 24 hs
- **WHEN** el usuario hace clic en "Ventas de las últimas 24 hs"
- **THEN** redirige a /last-sales

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

### Requirement: Ventas de las últimas 24 horas
La página de ventas recientes SHALL mostrar una tabla simple con todas las ventas realizadas durante las últimas 24 horas, siguiendo el patrón de implementación de `Proyecto_lector_de_codigo_barras/frontend/src/Components/SalesHistory`. Esta página es independiente del historial con calendario en `/sales-history`.

#### Scenario: Carga inicial
- **WHEN** el usuario navega a `/last-sales`
- **THEN** la pantalla carga automáticamente las ventas recientes desde `/api/sales/recent`
- **AND** muestra el título "Ventas de las últimas 24 hs"
- **AND** muestra una descripción breve indicando que muestra las ventas cerradas de las últimas 24 horas

#### Scenario: Tabla con ventas recientes
- **WHEN** la API retorna una lista con ventas recientes
- **THEN** se muestra una tabla responsive
- **AND** la tabla incluye columnas para ID, Fecha, Total, Items y Estado
- **AND** cada fila muestra `sale.id`, `sale.created_at`, `sale.total_price`, `sale.items.length` y `sale.state`

#### Scenario: Estado de carga
- **WHEN** la pantalla está esperando la respuesta de la API
- **THEN** muestra el mensaje "Cargando ventas..."

#### Scenario: Error de carga
- **WHEN** la API falla o la respuesta no puede procesarse
- **THEN** muestra el mensaje "No se pudo cargar el historial de ventas"

#### Scenario: Sin ventas recientes
- **WHEN** la API retorna un array vacío
- **THEN** muestra el mensaje "No hay ventas registradas en las últimas 24 horas."

#### Implementation Notes
- La implementación SHALL reutilizar la estructura visual del proyecto de referencia: `Nav`, `option-panel`, bloque `box-title`, tabla dentro de `history-table-wrapper`, y estilos de tabla con borde redondeado, sombra suave y scroll horizontal en pantallas chicas.
- A diferencia del proyecto de referencia, este proyecto MUST usar `fetch` nativo para llamadas HTTP; no SHALL introducir `axios`.
- Esta pantalla no SHALL usar calendario ni modal; es una tabla simple que carga al entrar.

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
- **THEN** se muestra una animación de carga pulida: el avatar del bot con un anillo de glow pulsante y una burbuja "pensando" con puntos animados en onda usando los colores de la marca
- **AND** el botón de envío se deshabilita mostrando un spinner circular en lugar de texto
- **AND** la animación respeta la paleta púrpura y es fluida (sin saltos)

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

### Requirement: Refinamiento visual de inicio y chat

La página de inicio y el panel de chat SHALL tener un diseño refinado y cohesivo, manteniendo estrictamente la paleta púrpura existente (`--primary #7b46ff`, gradient a `#b565ff`, fondo `#f6f4ff`) y las variables de `App.css`. El refinamiento SHALL usar solo CSS/JSX, sin introducir librerías nuevas.

#### Scenario: Página de inicio pulida

- **WHEN** el usuario carga la página de inicio
- **THEN** ve el título "EscanApp" con una bajada (tagline) descriptiva
- **AND** las tres acciones se muestran como tarjetas con ícono y micro-interacciones (hover con elevación y brillo)
- **AND** el botón flotante del agente y su tooltip están visualmente refinados

#### Scenario: Paleta preservada

- **WHEN** se aplican los estilos refinados
- **THEN** los colores siguen siendo los de la paleta púrpura existente (no se introducen colores nuevos fuera de la paleta)
