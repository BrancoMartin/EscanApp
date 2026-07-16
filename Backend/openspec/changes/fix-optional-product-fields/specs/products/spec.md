## MODIFIED Requirements

### Requirement: Crear producto
El sistema SHALL permitir crear un producto con código de barras, nombre, precio y descripción opcional.

La **descripción** y el **proveedor** SHALL ser verdaderamente opcionales: si no se envían, o se envían vacíos, el producto SHALL crearse igual y esas columnas SHALL quedar en `NULL`. El sistema NO SHALL fallar por la ausencia de un campo declarado como opcional.

Los campos de texto (nombre, descripción, proveedor) SHALL normalizarse a minúsculas y sin espacios sobrantes antes de persistirse. Un texto vacío SHALL tratarse como ausente.

Cuando se invoquen los modelos de IA para inferir categorías y atributos, los campos de texto ausentes SHALL enviarse como string vacío y NUNCA como `null`.

#### Scenario: Creación exitosa
- **WHEN** se envía POST /api/products/ con barcode, name, price, description válidos
- **THEN** el sistema retorna 200 con id, name, price, barcode, description
- **AND** el producto se persiste en la base de datos

#### Scenario: Creación sin descripción ni proveedor
- **WHEN** se envía POST /api/products/ con barcode, name y price, pero SIN description y SIN proveedor
- **THEN** el sistema retorna 200 y el producto se persiste con `description = NULL` y `proveedor = NULL`
- **AND** el sistema NO retorna 500

#### Scenario: Descripción vacía
- **WHEN** se envía POST /api/products/ con `description: ""`
- **THEN** el producto se persiste con `description = NULL` (el string vacío se trata como ausente)

#### Scenario: Código de barras duplicado
- **WHEN** se envía POST /api/products/ con un barcode ya existente
- **THEN** el sistema retorna 400 con detalle "Ya existe un producto con ese codigo de barras"

#### Scenario: Nombre y descripción duplicados
- **WHEN** se envía POST /api/products/ con name y description idénticos a un producto existente
- **THEN** el sistema retorna 400 con detalle "Ya existe un producto con ese nombre y descripcion"

#### Scenario: Precio inválido
- **WHEN** se envía POST /api/products/ con price <= 0
- **THEN** el sistema retorna 400 con detalle "El precio del producto debe ser mayor que cero"

#### Scenario: Barcode vacío
- **WHEN** se envía POST /api/products/ con barcode vacío
- **THEN** el sistema retorna 400 con detalle "El codigo de barras es obligatorio"

### Requirement: Actualizar producto
El sistema SHALL permitir actualizar código de barras, nombre, precio, descripción y **proveedor** de un producto existente.

El precio SHALL tratarse como número: el sistema NO SHALL aplicarle operaciones de texto.

El proveedor enviado en el cuerpo de la petición SHALL persistirse; NO SHALL ignorarse en silencio.

#### Scenario: Actualización exitosa
- **WHEN** se envía PUT /api/products/{product_id} con datos válidos
- **THEN** el sistema retorna el producto actualizado
- **AND** el sistema NO retorna 500

#### Scenario: Actualización del precio
- **WHEN** se envía PUT /api/products/{product_id} con un price numérico
- **THEN** el precio se actualiza y el sistema NO falla al tratarlo como texto

#### Scenario: Actualización del proveedor
- **WHEN** se envía PUT /api/products/{product_id} con un proveedor
- **THEN** el proveedor queda persistido en el producto

#### Scenario: Producto no encontrado
- **WHEN** se envía PUT /api/products/{product_id} con un id inexistente
- **THEN** el sistema retorna 404 con detalle "Product not found"
