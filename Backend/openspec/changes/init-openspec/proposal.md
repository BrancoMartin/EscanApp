## Why

BarcodePaymentSystem es un proyecto brownfield que ya existe y funciona, pero carece de especificaciones formales. Sin un SDD vivo, los cambios futuros dependen de la memoria del desarrollador, el código no tiene trazabilidad contra requerimientos, y las decisiones de diseño quedan perdidas. OpenSpec resuelve esto gobernando el desarrollo mediante especificaciones versionadas junto al código, permitiendo cambios incrementales y trazables desde el día 1.

## What Changes

- Instalar OpenSpec CLI (@fission-ai/openspec)
- Inicializar estructura openspec/ con esquema spec-driven
- Configurar tool integration para Claude Code
- Crear openspec/config.yaml con el context del proyecto
- Hacer commit inicial de la estructura OpenSpec en git

## Capabilities

### New Capabilities
- `openspec-init`: Estructura base de OpenSpec (specs, changes, config.yaml) para gobernar el SDD del proyecto

### Modified Capabilities

*(Ninguna — es el cambio inicial, no hay specs previas)*

## Impact

- `Backend/` — nueva carpeta `openspec/` con config.yaml, specs/ y changes/
- `Backend/` — nuevo directorio `.claude/` con skills y comandos OPSX
- `package.json` (Backend) — puede modificarse si se añade openspec como dependencia
- No afecta código de runtime, ni base de datos, ni APIs existentes
