# Products Domain

## Requirements

### Requirement: Crear producto
El sistema SHALL permitir crear un producto con código de barras, nombre, precio y descripción opcional.

#### Scenario: Creación exitosa
- **WHEN** se envía POST /api/products/ con barcode, name, price, description válidos
- **THEN** el sistema retorna 200 con id, name, price, barcode, description
- **AND** el producto se persiste en la base de datos

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

### Requirement: Buscar producto por código de barras
El sistema SHALL permitir buscar un producto por su código de barras, retornando sus datos y la venta pendiente actualizada.

#### Scenario: Producto encontrado
- **WHEN** se envía GET /api/products/barcode/{barcode} con un barcode existente
- **THEN** el sistema retorna los datos del producto y la venta pendiente con el producto agregado
- **AND** si no existe venta pendiente, se crea una nueva

#### Scenario: Producto no encontrado
- **WHEN** se envía GET /api/products/barcode/{barcode} con un barcode inexistente
- **THEN** el sistema retorna 404 con detalle "Producto no encontrado"

### Requirement: Listar todos los productos
El sistema SHALL permitir listar todos los productos registrados.

#### Scenario: Listado exitoso
- **WHEN** se envía GET /api/products/
- **THEN** el sistema retorna un array con todos los productos

### Requirement: Actualizar producto
El sistema SHALL permitir actualizar código de barras, nombre, precio y descripción de un producto existente.

#### Scenario: Actualización exitosa
- **WHEN** se envía PUT /api/products/{product_id} con datos válidos
- **THEN** el sistema retorna el producto actualizado

#### Scenario: Producto no encontrado
- **WHEN** se envía PUT /api/products/{product_id} con un id inexistente
- **THEN** el sistema retorna 404 con detalle "Product not found"

### Requirement: Eliminar producto
El sistema SHALL permitir eliminar un producto por su ID.

#### Scenario: Eliminación exitosa
- **WHEN** se envía DELETE /api/products/{product_id}
- **THEN** el sistema retorna 200 con mensaje "Product deleted"

### Requirement: Atributos inferidos por IA al crear producto
El sistema SHALL extraer atributos del nombre y descripción del producto usando un modelo de IA (attribute_extractor), crear las categorías y atributos necesarios, y asociarlos al producto.

#### Scenario: Atributos inferidos y asignados
- **WHEN** se crea un producto con nombre y descripción
- **THEN** el sistema invoca attribute_extractor para extraer atributos
- **AND** crea las categorías y atributos que no existan
- **AND** asocia los atributos al producto mediante ProductAttribute

#### Scenario: Proveedor inferido desde campo dedicado
- **WHEN** se crea un producto con el campo proveedor informado
- **THEN** el sistema trata `proveedor` como una categoría de atributo del producto
- **AND** crea la categoría `proveedor` si no existe
- **AND** crea u obtiene un atributo cuyo nombre sea el valor ingresado en el campo proveedor
- **AND** el wrapper del agente garantiza este atributo aunque el modelo de IA omita proveedor en la respuesta
- **AND** asocia ese atributo al producto mediante ProductAttribute

#### Scenario: Proveedor no informado
- **WHEN** se crea un producto sin proveedor válido
- **THEN** el sistema no crea la categoría `proveedor`
- **AND** no asocia atributos de proveedor al producto
