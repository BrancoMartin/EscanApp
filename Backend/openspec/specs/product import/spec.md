# Product Import Domain

## Requirements

### Requirement: Importar productos desde Excel

El sistema SHALL permitir importar productos masivamente desde un archivo Excel.

#### Scenario: Importación exitosa

- **WHEN** el usuario selecciona un archivo Excel válido
- **THEN** el sistema procesa todas las filas
- **AND** crea los productos correspondientes en la base de datos
- **AND** retorna un resumen con:
  - cantidad de productos importados
  - cantidad de productos rechazados

#### Scenario: Archivo vacío

- **WHEN** el archivo no contiene productos
- **THEN** el sistema retorna `400`
- **AND** informa que el archivo no contiene registros válidos

#### Scenario: Archivo inválido

- **WHEN** el usuario intenta importar un archivo que no corresponde a un formato Excel válido
- **THEN** el sistema retorna `400`
- **AND** informa que el archivo es inválido

#### Scenario: Registros inválidos

- **WHEN** uno o más registros contienen errores
- **THEN** el sistema importa únicamente los registros válidos
- **AND** informa qué filas fueron rechazadas
- **AND** explica el motivo de cada rechazo

---

### Requirement: Importar productos desde archivos CSV

El sistema SHALL permitir importar productos desde archivos CSV exportados por otros sistemas.

#### Scenario: Importación exitosa

- **WHEN** el usuario carga un archivo CSV válido
- **THEN** el sistema crea los productos correspondientes
- **AND** retorna un resumen de la importación

#### Scenario: Archivo inválido

- **WHEN** el archivo CSV posee un formato incompatible
- **THEN** el sistema retorna `400`

---

### Requirement: Importar productos desde Maxirest

El sistema SHALL permitir importar productos exportados desde Maxirest.

#### Scenario: Importación exitosa

- **WHEN** el usuario carga un archivo compatible exportado desde Maxirest
- **THEN** el sistema interpreta el formato
- **AND** crea los productos correspondientes

#### Scenario: Archivo incompatible

- **WHEN** el archivo no corresponde al formato esperado
- **THEN** el sistema retorna `400`

---

### Requirement: Importar productos desde Tango

El sistema SHALL permitir importar productos exportados desde Tango.

#### Scenario: Importación exitosa

- **WHEN** el usuario carga un archivo compatible exportado desde Tango
- **THEN** el sistema interpreta el formato
- **AND** crea los productos correspondientes

#### Scenario: Archivo incompatible

- **WHEN** el archivo no corresponde al formato esperado
- **THEN** el sistema retorna `400`

---

### Requirement: Importar productos desde otros sistemas POS

El sistema SHALL permitir importar productos exportados desde otros sistemas POS compatibles.

#### Scenario: Importación exitosa

- **WHEN** el usuario carga un archivo compatible
- **THEN** el sistema convierte los datos al formato interno
- **AND** crea los productos correspondientes

#### Scenario: Sistema no soportado

- **WHEN** el usuario intenta importar un formato no soportado
- **THEN** el sistema retorna `400`
- **AND** informa que el sistema no es compatible

---

### Requirement: Mantener consistencia durante la importación

El sistema SHALL validar cada registro antes de almacenarlo.

#### Scenario: Todos los registros son válidos

- **WHEN** todos los productos cumplen las validaciones
- **THEN** todos los productos son almacenados

#### Scenario: Algunos registros contienen errores

- **WHEN** existen registros inválidos
- **THEN** únicamente se almacenan los registros válidos
- **AND** el sistema genera un reporte detallando:
  - fila
  - error encontrado
  - motivo del rechazo
