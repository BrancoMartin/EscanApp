## MODIFIED Requirements

### Requirement: 9 modelos especializados de IA

El sistema SHALL utilizar 9 modelos Ollama especializados, cada uno con un prompt específico para una tarea concreta.

Los 9 modelos SHALL derivar de un único modelo base: `qwen2.5:0.5b`. El modelo base SHALL ser coherente entre los Modelfiles (directiva `FROM`) y la configuración del cliente (`OLLAMA_MODEL`); NO SHALL declararse un modelo base distinto en la configuración del que usan los Modelfiles.

Los 9 modelos SHALL aprovisionarse automáticamente (ver capability `packaging`), tanto en la instalación como en el arranque de la aplicación. El usuario final NUNCA SHALL necesitar ejecutar `crear_modelos.bat` ni ningún comando de Ollama a mano.

#### Scenario: Modelos cargados

- **WHEN** el sistema inicia el agente
- **THEN** todos los modelos están disponibles para ser invocados según la intención detectada

#### Scenario: Modelo base coherente

- **WHEN** se inspecciona la directiva `FROM` de los 9 Modelfiles y el valor por defecto de `OLLAMA_MODEL`
- **THEN** todos referencian el mismo modelo base `qwen2.5:0.5b`

#### Scenario: Modelo faltante en el arranque

- **WHEN** la aplicación arranca y alguno de los 9 modelos no existe en Ollama
- **THEN** el sistema lo crea automáticamente en segundo plano a partir de su Modelfile, sin intervención del usuario
