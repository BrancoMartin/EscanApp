# Products Domain

## Requirements

### Requirement: Buscar producto por código de barras

El sistema SHALL permitir buscar un producto mediante su código de barras.

#### Scenario: Producto encontrado

- **WHEN** se envía `GET /api/products/barcode/{barcode}` con un código de barras existente
- **THEN** el sistema retorna los datos del producto
- **AND** agrega el producto a la venta pendiente actual
- **AND** si no existe una venta pendiente, crea una nueva automáticamente

#### Scenario: Producto no encontrado

- **WHEN** se envía `GET /api/products/barcode/{barcode}` con un código inexistente
- **THEN** el sistema retorna `404`
- **AND** el detalle indica `"Producto no encontrado"`

---

### Requirement: Listar productos

El sistema SHALL permitir listar todos los productos registrados.

#### Scenario: Listado exitoso

- **WHEN** se envía `GET /api/products`
- **THEN** el sistema retorna una colección con todos los productos

---

### Requirement: Obtener producto por ID

El sistema SHALL permitir obtener un producto específico mediante su identificador.

#### Scenario: Producto encontrado

- **WHEN** se envía `GET /api/products/{product_id}`
- **THEN** el sistema retorna toda la información del producto

#### Scenario: Producto inexistente

- **WHEN** se envía `GET /api/products/{product_id}` con un ID inexistente
- **THEN** el sistema retorna `404`

---

### Requirement: Actualizar producto

El sistema SHALL permitir modificar un producto existente.

#### Scenario: Actualización exitosa

- **WHEN** se envía `PUT /api/products/{product_id}` con información válida
- **THEN** el sistema actualiza el producto
- **AND** retorna la información actualizada

#### Scenario: Producto inexistente

- **WHEN** se intenta actualizar un producto inexistente
- **THEN** el sistema retorna `404`

---

### Requirement: Eliminar producto

El sistema SHALL permitir eliminar un producto.

#### Scenario: Eliminación exitosa

- **WHEN** se envía `DELETE /api/products/{product_id}`
- **THEN** el producto es eliminado
- **AND** el sistema retorna confirmación

#### Scenario: Producto inexistente

- **WHEN** se intenta eliminar un producto inexistente
- **THEN** el sistema retorna `404`
