## 1. Normalización de entrada

- [x] 1.1 Helper de normalización en `controller_products.py`: trim + minúsculas, y `None` si el valor está ausente o vacío (sin `isinstance()`)
- [x] 1.2 Helper para los modelos de IA: string vacío en vez de `None` (los modelos esperan texto)

## 2. POST /api/products/ (crear)

- [x] 2.1 Normalizar `name`, `description` y `proveedor` una sola vez, al principio de `create`
- [x] 2.2 Pasar los valores normalizados a `service.create` (sin `.lower()` sobre posibles `None`)
- [x] 2.3 Pasar string vacío a `create_categories()` y `attribute_extractor()` cuando falte el dato
- [x] 2.4 Guardar `proveedor` normalizado

## 3. PUT /api/products/{id} (actualizar)

- [x] 3.1 Quitar `.lower()` del precio (es un float: siempre reventaba)
- [x] 3.2 Normalizar los campos de texto sin romper con `None`
- [x] 3.3 Persistir `proveedor` (hoy se acepta en el body y se ignora)

## 4. ProductService

- [x] 4.1 `create()`: tolerante a `description` / `proveedor` en `None`
- [x] 4.2 `update()`: aceptar y persistir `proveedor`; no aplicar `.lower()` a valores `None`

## 5. Verificación

- [x] 5.1 `python -m py_compile` de los archivos tocados
- [x] 5.2 Crear producto SIN descripción ni proveedor → 200, columnas en NULL
- [x] 5.3 Crear producto CON todos los campos → 200 (no se rompió lo que ya andaba)
- [x] 5.4 Actualizar producto (incluido el precio) → 200, sin 500
- [x] 5.5 Actualizar el proveedor → queda persistido
- [x] 5.6 Sin `isinstance()` en el código tocado
- [x] 5.7 `openspec validate fix-optional-product-fields`
