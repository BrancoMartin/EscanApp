## Context

BarcodePaymentSystem es un proyecto brownfield con stack definido (FastAPI + React + SQLite + Ollama). No existe actualmente ningún sistema de especificaciones ni SDD formal. OpenSpec se introduce como herramienta de governance de desarrollo, no como dependencia de runtime.

El proyecto tiene una estructura de capas clara: API Routes → Services → Repositories → Models, más un frontend React con Vite. OpenSpec vivirá junto al código en el repo, en una carpeta `openspec/` dentro de `Backend/`.

## Goals / Non-Goals

**Goals:**
- Proveer estructura openspec/ con esquema spec-driven funcional
- Configurar integración con Claude Code (skills + comandos OPSX)
- Capturar el context del proyecto en config.yaml para que los agentes IA tengan contexto preciso
- Establecer el patrón de trabajo: propose → design/specs → tasks → apply → verify → archive

**Non-Goals:**
- NO documentar todo el código existente (solo el cambio actual)
- NO modificar runtime, base de datos, APIs, ni frontend
- NO migrar datos ni cambiar configuraciones existentes

## Decisions

| Decisión | Opción elegida | Alternativas | Razón |
|----------|---------------|--------------|-------|
| Ubicación de openspec/ | Dentro de Backend/ | Raíz del repo | El stack de backend es Python y OpenSpec es Node.js; mantenerlo en Backend/ evita mezclar toolchains. También es donde se ejecutarán los comandos OPSX. |
| Config context en config.yaml | Contexto técnico detallado (stack, arquitectura, naming, testing) | Contexto mínimo | Un agente IA necesita contexto preciso para generar specs y código coherentes. El note existente ya define este contexto. |
| Tool integration | Claude Code | Solo CLI | Las skills y comandos OPSX permiten flujo interactivo sin recordar comandos CLI. |

## Risks / Trade-offs

- **[Herramienta externa]** OpenSpec CLI es un paquete npm. Si el proyecto se mueve a otro entorno, hay que reinstalarlo. → Mitigación: documentar en README o automatizar en setup script.
- **[Node.js en proyecto Python]** Introduce una dependencia de toolchain Node.js en un proyecto mayoritariamente Python. → Mitigación: solo es dependencia de desarrollo, no de runtime.
- **[Brownfield incompleto]** La primera vez que se use OpenSpec, el contexto capturado puede no cubrir todos los detalles. → Mitigación: usar /opsx:explore antes de proponer cambios para investigar el código actual.
