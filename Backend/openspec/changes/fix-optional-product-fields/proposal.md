## Why

Dos endpoints del dominio `products` crashean con **500 Internal Server Error** por llamar `.lower()` sobre valores que no son strings. Se detectaron probando el ejecutable empaquetado (cambio `windows-installer`).

**1. `POST /api/products/` revienta si el producto no trae descripción o proveedor.**

`ProductInput` declara `description: Optional[str] = None` y `proveedor: Optional[str] = None`, y la tabla `products` permite `NULL` en ambas columnas. Pero el controlador hace:

```python
service.create(data.barcode, data.name.lower(), data.price, data.description.lower(), data.proveedor.lower())
```

Si el usuario omite la descripción → `AttributeError: 'NoneType' object has no attribute 'lower'` → 500. El mismo error se repite en las llamadas a `create_categories()` y `attribute_extractor()`, y otra vez dentro de `ProductService.create()`.

Es contradictorio: el sistema **declara** los campos como opcionales y después **explota** cuando se los omite. Y es exactamente el flujo del agente de IA, que puede crear productos sin proveedor.

**2. `PUT /api/products/{product_id}` está roto SIEMPRE, con cualquier payload.**

```python
service.update(product_id, data.barcode.lower(), data.name.lower(), data.price.lower(), data.description.lower())
```

`price` es un `float`. `float.lower()` no existe: `AttributeError: 'float' object has no attribute 'lower'`. El endpoint de actualización **nunca funcionó**.

Además, `update` acepta `proveedor` en el body y lo **ignora en silencio**: nunca se persiste.

## What Changes

- **Normalización en un solo lugar.** Los campos de texto se normalizan (trim + minúsculas) en el borde de la API, con una función que devuelve `None` cuando el valor está ausente o vacío. Un string vacío `""` se trata como ausente, para no guardar basura.
- `POST /api/products/` SHALL aceptar productos sin descripción y sin proveedor, persistiendo `NULL` en esas columnas.
- Las llamadas a los modelos de IA (`create_categories`, `attribute_extractor`) SHALL recibir un string vacío en vez de `None` cuando el campo falta: los modelos esperan texto, no `null`.
- `PUT /api/products/{product_id}` SHALL dejar de llamar `.lower()` sobre el precio, y SHALL persistir el `proveedor`.
- `ProductService.create()` y `ProductService.update()` SHALL ser defensivos ante `None` en los campos opcionales, dado que también los llama el agente de IA.
- No se usa `isinstance()` (regla del proyecto).

## Capabilities

### Modified Capabilities
- `products`: crear producto con descripción y/o proveedor ausentes deja de fallar; actualizar producto deja de fallar siempre y ahora persiste el proveedor.

## Impact

- `Backend/api/routes/controller_products.py` — normalización de entrada en `create` y `update`.
- `Backend/services/product_service.py` — `create` y `update` tolerantes a `None`.
- **No cambia** el contrato HTTP: los mismos endpoints, los mismos campos, los mismos códigos de error. Solo dejan de tirar 500.
- **No cambia** el frontend: hoy manda siempre los cinco campos, así que su comportamiento es idéntico.
- **No cambia** la base de datos: las columnas ya eran `nullable=True`.
