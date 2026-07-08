## Why

Cuando el usuario envía un mensaje al agente IA, la espera se muestra con un indicador de tres puntos muy básico. El usuario pidió una **animación de carga más linda** y, además, **mejorar el diseño general de la página** respetando la paleta púrpura actual (`#7b46ff` → `#b565ff`, fondo `#f6f4ff`).

## What Changes

- **Animación de carga del agente**: reemplazar los tres puntos planos por una burbuja "pensando" pulida: avatar del bot con anillo de glow pulsante, burbuja con degradé sutil (shimmer) y puntos animados en onda con los colores de la marca. El botón de envío muestra un spinner circular en vez de "...".
- **Refinamiento visual de la página de inicio**: agregar una bajada (tagline) bajo el título, tarjetas de acción con ícono y micro-interacciones más pulidas, y refinar el botón flotante y el tooltip del agente.
- **Refinamiento del panel de chat**: sombras, encabezado con brillo sutil y burbujas de mensaje más prolijas, sin cambiar la paleta.
- Todo SHALL respetar la paleta y variables existentes (`--primary`, `--primary-dark`, etc.). No se introducen librerías nuevas (solo CSS/JSX).

## Capabilities

### Modified Capabilities
- `ui`: se mejora la animación de carga del chat y el refinamiento visual de inicio/chat, manteniendo el tema púrpura.

## Impact

- `Frontend/src/Components/AgentChat/AgentChat.css` — animación de carga y pulido del panel.
- `Frontend/src/Components/AgentChat/AgentChat.jsx` — spinner en botón de envío y burbuja "pensando".
- `Frontend/src/Pages/start.css`, `Frontend/src/Pages/start.jsx` — tagline, tarjetas con ícono, micro-interacciones.
- No cambia backend, base de datos ni contrato HTTP.
