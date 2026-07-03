# Categories & Attributes Domain

## Requirements

### Requirement: Crear categoría

El sistema SHALL permitir crear una categoría con nombre único.

#### Scenario: Creación exitosa

- **WHEN** se envía POST /api/categories con name nuevo
- **THEN** el sistema retorna 200 con id, name, created_at

#### Scenario: Categoría duplicada

- **WHEN** se envía POST /api/categories con un name ya existente
- **THEN** el sistema retorna 400 con detalle "La categoria '{name}' ya existe"

### Requirement: Listar categorías

El sistema SHALL permitir listar todas las categorías.

#### Scenario: Listado exitoso

- **WHEN** se envía GET /api/categories cuando el usuario le dice al agente "mostrame las categorias que existen en la bd"
- **THEN** el sistema retorna un array con todas las categorías (id, name, created_at)
- **AND** las categorias se mostrarán en el chat del agente de ia

### Requirement: Eliminar categoría

El sistema SHALL permitir eliminar una categoría y todos sus atributos asociados.

#### Scenario: Eliminación exitosa

- **WHEN** se envía DELETE /api/categories/{category_id}
- **THEN** el sistema elimina la categoría y sus atributos
- **AND** retorna 200 con mensaje "Categoria eliminada"

#### Scenario: Categoría no encontrada

- **WHEN** se envía DELETE /api/categories/{category_id} con id inexistente
- **THEN** el sistema retorna 404 con detalle "Categoria no encontrada"

### Requirement: Crear atributo

El sistema SHALL permitir crear un atributo dentro de una categoría existente, con nombre único por categoría.

#### Scenario: Creación exitosa

- **WHEN** se envía POST /api/attributes con category_id y name válidos
- **THEN** el sistema retorna 200 con id, category_id, name, created_at

#### Scenario: Categoría no existe

- **WHEN** se envía POST /api/attributes con category_id inexistente
- **THEN** el sistema retorna 404 con detalle "Categoria no encontrada"

#### Scenario: Atributo duplicado en la base de datos

- **WHEN** se envía POST /api/attributes con category_id y name ya existentes en la base de datos
- **THEN** el sistema retorna 400 con detalle "El atributo '{name}' ya existe en en la base de datos y pertenece a la categoria 'category'"

### Requirement: Listar atributos

El sistema SHALL permitir listar atributos, opcionalmente filtrados por categoría.

#### Scenario: Listar todos los atributos

- **WHEN** se envía GET /api/attributes sin parámetros, por que el usuario en le dice al agente "mostrame los atributos que estan en la base de datos"
- **THEN** el sistema retorna todos los atributos
- **AND** le envia los atributos al usuario por el chat del agente de ia

#### Scenario: Listar atributos por categoría

- **WHEN** se envía GET /api/attributes?category_id={id}, por que el usuario en le dice al agente "mostrame los atributos que tiene la categoria '{category}'"
- **THEN** el sistema retorna solo los atributos de esa categoría
- **AND** los muestra en el chat del agente de ia

### Requirement: Obtener o crear categoría (service layer)

El servicio de categorías SHALL proporcionar un método get_or_create que busque por nombre y cree la categoría si no existe.

#### Scenario: Proveedor como categoría de atributo

- **WHEN** se crea un producto con el campo proveedor informado y la categoría `proveedor` no existe
- **THEN** el sistema crea la categoría `proveedor`
- **AND** la creación de la categoría `proveedor` SHALL estar garantizada por el wrapper del agente aunque el modelo de IA omita esa categoría
- **AND** el nombre real del proveedor no se guarda como categoría
- **AND** el nombre real del proveedor se guarda como atributo dentro de la categoría `proveedor`

#### Scenario: Categoría existente

- **WHEN** se invoca get_or_create_category con un nombre existente, porque el usuario le escribe al agente de ia que le cree la categoria con el nombre '{category}' y la categoria esta en la base de datos
- **THEN** retorna la categoría existente sin crear duplicados
- **AND** lo muestra en el chat del agente de ia

#### Scenario: Categoría nueva

- **WHEN** se invoca get_or_create_category con un nombre nuevo, porque el usuario le escribe al agente de ia que le cree la categoria con nombre '{category}' y la categoria no esta en la base de datos
- **THEN** crea y retorna la nueva categoría
- **AND** la muestra en el chat del agente de ia

### Requirement: Obtener o crear atributo (service layer)

El servicio de atributos SHALL proporcionar un método get_or_create que busque por category_id y name, y cree el atributo si no existe.

#### Scenario: Atributo existente

- **WHEN** se invoca get_or_create_attribute con category_id y name existentes, por que el usuario le dice al agente que cree el atributo con el nombre '{attribute}' y el atributo esta en la base de datos
- **THEN** retorna el atributo existente

#### Scenario: Atributo nuevo

- **WHEN** se invoca get_or_create_attribute con category_id y name nuevos, por que el usuario le dice al agente que cree el atributo con el nombre '{attribute}' y el atributo no esta en la base de datos
- **THEN** crea y retorna el nuevo atributo

### Requirement: Asignar atributo a producto

El sistema SHALL permitir asociar un atributo a un producto mediante ProductAttribute.

#### Scenario: Asignación exitosa

- **WHEN** se asocia un atributo a un producto
- **THEN** se crea el registro en product_attribute
- **AND** se incrementa amount_products en el atributo

#### Scenario: Asignación duplicada

- **WHEN** se intenta asignar un atributo ya asociado al producto
- **THEN** retorna la asociación existente sin crear duplicado

### Requirement: Productos por atributo

El sistema SHALL permitir obtener productos que tengan un atributo específico.

#### Scenario: Productos encontrados

- **WHEN** se envía GET /api/products/{attribute_id}
- **THEN** retorna los productos que tienen ese atributo
