## ADDED Requirements

### Requirement: OpenSpec CLI instalado
El sistema SHALL tener OpenSpec CLI (npm package @fission-ai/openspec) instalado globalmente en el entorno de desarrollo.

#### Scenario: Instalación correcta
- **WHEN** se ejecuta `npm list -g @fission-ai/openspec`
- **THEN** el paquete aparece en la lista de paquetes globales de npm

### Requirement: Estructura openspec/ creada
El sistema SHALL tener una carpeta `openspec/` en la raíz del backend con subcarpetas `specs/`, `changes/` y archivo `config.yaml`.

#### Scenario: Verificar estructura openspec
- **WHEN** se listan los contenidos de `openspec/`
- **THEN** existen los directorios `specs/` y `changes/`
- **AND** existe el archivo `config.yaml`

### Requirement: Config context definido
El archivo `openspec/config.yaml` SHALL contener el contexto técnico del proyecto: stack, arquitectura, base de datos, IA, frontend, estilo API, manejo de errores, naming y testing.

#### Scenario: Config contiene stack
- **WHEN** se lee `openspec/config.yaml`
- **THEN** el campo `context` menciona FastAPI, SQLAlchemy, SQLite, React 19, Vite 8, Ollama, LangChain

### Requirement: Tool integration configurada
El sistema SHALL tener integración con Claude Code mediante skills y comandos OPSX en `.claude/`.

#### Scenario: Skills OPSX presentes
- **WHEN** se listan los skills en `.claude/skills/`
- **THEN** existen skills para propose, apply, explore, sync, archive
