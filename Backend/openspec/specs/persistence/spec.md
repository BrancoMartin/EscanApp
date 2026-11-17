# persistence Specification

## Purpose

Define cómo evoluciona y se protege el esquema de la base local de EscanApp: el esquema cambia únicamente por migraciones versionadas de Alembic; una base de cliente existente se adopta sin perder datos, con copia de seguridad verificada antes de tocar nada; y una base desconocida detiene el arranque en lugar de modificarse.
## Requirements
### Requirement: Las migraciones son el único mecanismo de evolución del esquema

El sistema SHALL definir el esquema de la base de datos mediante migraciones versionadas y ordenadas. El sistema NO SHALL usar `Base.metadata.create_all()` ni ningún archivo de base precargado como mecanismo de creación o de evolución del esquema. Toda modificación futura del esquema —agregar una tabla, una columna, un índice o una restricción— SHALL expresarse como una migración nueva.

La primera migración (revisión base) SHALL reproducir exactamente el esquema de la versión 1.0.1: las tablas `products`, `categories`, `attributes`, `product_attributes`, `sales` y `sale_items`, con sus índices y restricciones únicas tal como existen hoy.

#### Scenario: El esquema nace de las migraciones

- **WHEN** se crea una base de datos desde cero
- **THEN** las 6 tablas, sus índices y sus restricciones son creados por la revisión base
- **AND** el esquema resultante es equivalente al de la versión 1.0.1
- **AND** ningún componente de la aplicación crea tablas por fuera de las migraciones

#### Scenario: Un cambio de modelo sin migración es detectable

- **WHEN** se compara el estado de los modelos SQLAlchemy contra una base que está en la última revisión
- **THEN** no se detecta ninguna diferencia de esquema
- **AND** una diferencia detectada indica que falta escribir una migración

### Requirement: Instalación nueva

En una instalación donde la base de datos no existe, el sistema SHALL crearla aplicando todas las migraciones en orden hasta la última revisión, de forma automática y sin intervención del usuario.

#### Scenario: Primer arranque de un cliente nuevo

- **WHEN** la aplicación arranca y el archivo de base de datos no existe
- **THEN** el sistema crea la base y aplica todas las migraciones hasta la última revisión
- **AND** la base queda registrada en esa revisión
- **AND** la aplicación arranca normalmente

#### Scenario: Una instalación nueva es indistinguible de una actualizada

- **WHEN** se compara el esquema de una instalación nueva con el de una instalación existente que fue migrada a la misma revisión
- **THEN** ambos esquemas son equivalentes

### Requirement: Adopción de instalaciones existentes sin pérdida de datos

El sistema SHALL reconocer una base de datos creada por una versión anterior a las migraciones (sin registro de versión de esquema) y adoptarla **sellándola** en la revisión base, sin ejecutar esa revisión sobre ella. Recién después SHALL aplicar las migraciones posteriores.

El sistema NO SHALL borrar, recrear ni vaciar una base existente en ningún caso.

#### Scenario: Cliente 1.0.x que actualiza

- **WHEN** la aplicación arranca sobre una base que tiene las tablas del producto pero no tiene registro de versión de esquema
- **THEN** el sistema la sella en la revisión base sin ejecutarla
- **AND** aplica las migraciones posteriores que correspondan
- **AND** todos los productos, ventas, categorías y atributos existentes se conservan sin alteración

#### Scenario: La adopción ocurre una sola vez

- **WHEN** una base ya fue sellada y la aplicación vuelve a arrancar
- **THEN** el sistema la trata como una base ya versionada
- **AND** no vuelve a sellarla

#### Scenario: Base ya al día

- **WHEN** la aplicación arranca sobre una base que ya está en la última revisión
- **THEN** el sistema no aplica ninguna migración
- **AND** la aplicación arranca normalmente

### Requirement: Ejecución automática al iniciar la aplicación

El sistema SHALL evaluar y aplicar las migraciones pendientes automáticamente durante el arranque, antes de que cualquier operación de lectura o escritura toque la base de datos. El usuario del comercio NO SHALL tener que ejecutar ningún comando, script ni acción manual.

#### Scenario: Migración pendiente al abrir la aplicación

- **WHEN** el usuario abre la aplicación y hay migraciones sin aplicar
- **THEN** el sistema las aplica antes de atender la primera consulta
- **AND** el usuario no necesita hacer nada

#### Scenario: Ninguna operación precede a la migración

- **WHEN** la aplicación está arrancando
- **THEN** ninguna sesión de base de datos se abre para operaciones de negocio antes de que las migraciones hayan terminado

### Requirement: Ninguna operación destructiva sin una migración explícita

El sistema NO SHALL modificar la estructura ni el contenido de la base por fuera de una migración declarada. Ante una base que no puede clasificar —que existe, no tiene registro de versión de esquema y no contiene las tablas esperadas del producto— el sistema SHALL abortar el arranque sin escribir absolutamente nada en ella, y SHALL registrar el motivo.

#### Scenario: Base desconocida o corrupta

- **WHEN** la aplicación encuentra una base sin registro de versión y sin las tablas esperadas del producto
- **THEN** el sistema no modifica el archivo
- **AND** no aplica ni sella ninguna revisión
- **AND** aborta el arranque informando el motivo

#### Scenario: Fallo durante una migración

- **WHEN** una migración falla a mitad de camino
- **THEN** los cambios de esa migración se revierten y la base queda en la revisión anterior
- **AND** la aplicación no continúa arrancando con un esquema a medio migrar
- **AND** se informa el error al usuario indicando dónde está el detalle y que sus datos están intactos

### Requirement: Respaldo previo a migrar

Antes de aplicar migraciones sobre una base de datos que contiene datos, el sistema SHALL crear una copia de seguridad del archivo dentro de la carpeta de datos del usuario, identificada por la revisión de origen y la fecha. El sistema SHALL conservar las copias más recientes y descartar las más antiguas para no consumir el disco indefinidamente.

#### Scenario: Se respalda antes de migrar una base con datos

- **WHEN** hay migraciones pendientes sobre una base que contiene datos
- **THEN** el sistema copia la base antes de aplicarlas
- **AND** la copia queda en la carpeta de datos del usuario, identificable por revisión y fecha

#### Scenario: No se respalda sin motivo

- **WHEN** no hay migraciones pendientes, o la base está vacía
- **THEN** el sistema no crea ninguna copia

#### Scenario: Recuperación ante una migración fallida

- **WHEN** una actualización dejó la base en un estado inutilizable
- **THEN** restaurar la copia previa devuelve la base al estado anterior a la migración

### Requirement: Versión del esquema consultable

El sistema SHALL registrar en la propia base la revisión de esquema en la que se encuentra, y SHALL exponerla para diagnóstico: en el estado del sistema que ya reporta la versión del producto, y en el registro de arranque de la aplicación.

#### Scenario: Consultar el estado del sistema

- **WHEN** se consulta el estado del sistema
- **THEN** la respuesta incluye la revisión de esquema de esa instalación
- **AND** indica si está o no en la última revisión

#### Scenario: Diagnóstico remoto de un cliente

- **WHEN** hay que determinar en qué estado quedó la base de una instalación de un cliente
- **THEN** la revisión de esquema aparece en el registro de arranque de la aplicación

### Requirement: Compatibilidad con SQLite

Las migraciones SHALL escribirse de forma compatible con SQLite, contemplando que SQLite no admite eliminar ni alterar columnas mediante `ALTER TABLE`. El sistema SHALL usar el modo de migración por lotes (recreación de tabla con copia de datos) para toda operación que SQLite no soporte de forma nativa.

#### Scenario: Migración que elimina o altera una columna

- **WHEN** una migración futura necesita eliminar una columna o cambiar su tipo
- **THEN** la migración se ejecuta correctamente sobre SQLite recreando la tabla
- **AND** los datos de las columnas conservadas se preservan

#### Scenario: Migración que agrega una columna

- **WHEN** una migración futura agrega una columna
- **THEN** la migración se ejecuta correctamente sobre SQLite
- **AND** las filas existentes conservan sus valores

### Requirement: Funcionamiento en desarrollo y en el ejecutable empaquetado

El sistema SHALL aplicar migraciones con el mismo comportamiento tanto ejecutando el código fuente en desarrollo como dentro del ejecutable generado con PyInstaller. Los scripts de migración SHALL viajar dentro del producto empaquetado como recurso de solo lectura, resueltos por la misma abstracción de rutas que el resto de los recursos. El proceso de construcción del release SHALL fallar de forma explícita si los scripts de migración no están disponibles para empaquetar.

#### Scenario: Migración en desarrollo

- **WHEN** la aplicación se ejecuta desde el código fuente
- **THEN** las migraciones se localizan y se aplican correctamente

#### Scenario: Migración en el ejecutable instalado

- **WHEN** la aplicación se ejecuta desde el ejecutable instalado en la máquina de un cliente
- **THEN** las migraciones se localizan dentro del producto empaquetado y se aplican correctamente
- **AND** la base se crea o se actualiza en la carpeta de datos escribible del usuario, no junto al ejecutable

#### Scenario: Build sin migraciones

- **WHEN** se intenta construir el release y los scripts de migración no están presentes
- **THEN** la construcción se detiene con un error explícito
- **AND** no se genera un instalador incompleto

