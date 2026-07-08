## MODIFIED Requirements

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

## ADDED Requirements

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
