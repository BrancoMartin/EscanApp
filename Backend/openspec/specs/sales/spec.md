# Sales Domain

## Requirements

### Requirement: Crear venta
El sistema SHALL permitir crear una venta con estado "pending", calculando el precio total a partir de sus items.

#### Scenario: Creación exitosa
- **WHEN** se envía POST /api/sales/ con items (product_id, quantity, unit_price)
- **THEN** el sistema crea una venta en estado "pending"
- **AND** calcula total_price como suma de quantity * unit_price
- **AND** retorna la venta con sus items

### Requirement: Validar que solo exista una venta pending
El sistema SHALL rechazar la creación de una nueva venta si ya existe una en estado "pending", obligando al usuario a cerrar o cancelar la pendiente antes de iniciar otra.

#### Scenario: Rechazar creación con pending existente
- **WHEN** se envía POST /api/sales/ con items y ya existe una venta en estado "pending"
- **THEN** el sistema retorna error 409 (Conflict)
- **AND** el mensaje informa: "Ya existe una venta pendiente. Debes cerrarla o cancelarla antes de crear una nueva."

#### Scenario: Escaneo con pending existente
- **WHEN** se escanea un barcode y ya existe una venta en estado "pending"
- **THEN** el sistema NO crea una nueva venta
- **AND** agrega el producto a la venta pendiente existente (mismo comportamiento que los escenarios de escaneo con venta pendiente)

### Requirement: Obtener venta pendiente
El sistema SHALL retornar la venta pendiente más reciente.

#### Scenario: Venta pendiente existe
- **WHEN** se envía GET /api/sales/pending
- **THEN** retorna la venta en estado "pending" más reciente

#### Scenario: No hay venta pendiente
- **WHEN** no existe ninguna venta pendiente
- **THEN** GET /api/sales/pending retorna null

### Requirement: Listar todas las ventas
El sistema SHALL permitir listar todas las ventas registradas.

#### Scenario: Listado exitoso
- **WHEN** se envía GET /api/sales/
- **THEN** retorna un array con todas las ventas incluyendo items

### Requirement: Listar ventas de las últimas 24 horas
El sistema SHALL permitir consultar las ventas registradas durante las últimas 24 horas para alimentar la página web de historial reciente.

#### Scenario: Listado reciente exitoso
- **WHEN** se envía GET /api/sales/recent
- **THEN** retorna un array con las ventas cuyo `created_at` sea mayor o igual a la fecha/hora actual menos 24 horas
- **AND** cada venta incluye `id`, `state`, `total_price`, `created_at` e `items`
- **AND** la cantidad de items mostrable por la UI se calcula como `items.length` sin requerir un campo persistido adicional

#### Scenario: Sin ventas recientes
- **WHEN** se envía GET /api/sales/recent y no hay ventas en las últimas 24 horas
- **THEN** retorna un array vacío

#### Scenario: Orden del listado reciente
- **WHEN** existen múltiples ventas recientes
- **THEN** retorna primero las ventas más nuevas, ordenadas por `created_at` descendente

#### Implementation Notes
- La ruta `/api/sales/recent` MUST declararse antes de `/api/sales/{sale_id}` para evitar que FastAPI interprete `recent` como un `sale_id`.
- Para que el filtro de 24 horas sea real, las ventas nuevas MUST guardar `created_at` con fecha y hora (`datetime.now()`), no solo con fecha (`date.today()`).
- Esta consulta no SHALL modificar ventas, items ni productos; es solo lectura.

### Requirement: Obtener detalle de venta
El sistema SHALL permitir obtener el detalle completo de una venta por su ID.

#### Scenario: Venta encontrada
- **WHEN** se envía GET /api/sales/{sale_id}
- **THEN** retorna la venta con sus items, producto, cantidades y subtotales

#### Scenario: Venta no encontrada
- **WHEN** se envía GET /api/sales/{sale_id} con id inexistente
- **THEN** retorna 404 con detalle "Sale not found"

### Requirement: Cerrar venta
El sistema SHALL permitir cerrar una venta, cambiando su estado de "pending" a "closed".

#### Scenario: Cierre exitoso
- **WHEN** se envía POST /api/sales/{sale_id}/close
- **THEN** la venta cambia a estado "closed"
- **AND** retorna la venta actualizada

#### Scenario: Venta no encontrada
- **WHEN** se envía POST /api/sales/{sale_id}/close con id inexistente
- **THEN** retorna 404 con detalle "No se pudo cerrar la venta"

### Requirement: Cancelar venta completa
El sistema SHALL permitir eliminar una venta completa (hard delete).

#### Scenario: Cancelación exitosa
- **WHEN** se envía DELETE /api/sales/{sale_id}
- **THEN** la venta se elimina de la base de datos
- **AND** retorna 200 con mensaje de éxito

### Requirement: Cancelar item individual
El sistema SHALL permitir cancelar un item específico de una venta. Si el item tiene quantity > 1, decrementa en 1. Si quantity = 1, elimina el item.

#### Scenario: Cancelar item con cantidad > 1
- **WHEN** se envía PUT /api/sales/{sale_id}/items/{item_id} y el item tiene quantity > 1
- **THEN** decrementa quantity en 1
- **AND** actualiza total_price

#### Scenario: Cancelar último item (quantity = 1)
- **WHEN** se envía PUT /api/sales/{sale_id}/items/{item_id} y el item es el último
- **THEN** elimina el item de la venta
- **AND** actualiza total_price

#### Scenario: Item no encontrado
- **WHEN** se envía PUT /api/sales/{sale_id}/items/{item_id} con item inexistente
- **THEN** retorna 404 con detalle "Item not found"

### Requirement: Escanear producto a venta pendiente
El sistema SHALL permitir escanear un código de barras para agregar el producto a la venta pendiente. Si el producto ya está en la venta, incrementa su cantidad.

#### Scenario: Producto nuevo en venta
- **WHEN** se escanea un barcode de un producto no incluido en la venta pendiente
- **THEN** agrega un nuevo item con quantity = 1

#### Scenario: Producto ya en venta
- **WHEN** se escanea un barcode de un producto ya incluido en la venta pendiente
- **THEN** incrementa quantity en 1

#### Scenario: Sin venta pendiente
- **WHEN** se escanea un barcode y no hay venta pendiente
- **THEN** crea una nueva venta en estado "pending"
- **AND** agrega el producto como item

### Requirement: Historial de ventas por fecha
El sistema SHALL permitir consultar ventas filtradas por fecha.

#### Scenario: Fecha con ventas
- **WHEN** se envía GET /api/sales/date/{date} con formato YYYY-MM-DD
- **THEN** retorna las ventas de esa fecha

#### Scenario: Fecha sin ventas
- **WHEN** se envía GET /api/sales/date/{date} con una fecha sin ventas
- **THEN** retorna un array vacío

#### Scenario: Formato de fecha inválido
- **WHEN** se envía GET /api/sales/date/{date} con formato inválido
- **THEN** retorna error con detalle "Invalid date format. Use YYYY-MM-DD."
