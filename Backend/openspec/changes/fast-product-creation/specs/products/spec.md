## MODIFIED Requirements

### Requirement: Crear producto
El sistema SHALL permitir crear un producto con código de barras, nombre, precio y descripción opcional.

La **descripción** y el **proveedor** SHALL ser verdaderamente opcionales: si no se envían, o se envían vacíos, el producto SHALL crearse igual y esas columnas SHALL quedar en `NULL`. El sistema NO SHALL fallar por la ausencia de un campo declarado como opcional.

Los campos de texto (nombre, descripción, proveedor) SHALL normalizarse a minúsculas y sin espacios sobrantes antes de persistirse. Un texto vacío SHALL tratarse como ausente.

Cuando se invoquen los modelos de IA para inferir categorías y atributos, los campos de texto ausentes SHALL enviarse como string vacío y NUNCA como `null`.

La respuesta del endpoint SHALL emitirse apenas el producto está persistido. El sistema NO SHALL bloquear la respuesta esperando la inferencia de categorías o atributos por IA: ese trabajo es accesorio al alta y el usuario no lo ve en pantalla.

#### Scenario: Creación exitosa
- **WHEN** se envía POST /api/products/ con barcode, name, price, description válidos
- **THEN** el sistema retorna 200 con id, name, price, barcode, description
- **AND** el producto se persiste en la base de datos

#### Scenario: Respuesta inmediata, sin esperar a la IA
- **WHEN** se envía POST /api/products/ con datos válidos
- **THEN** el sistema retorna 200 apenas el producto está persistido, sin haber invocado ningún modelo de IA
- **AND** el tiempo de respuesta es del orden de una escritura en base (< 0.5 s), no del orden de una inferencia (> 5 s)

#### Scenario: Creación sin descripción ni proveedor
- **WHEN** se envía POST /api/products/ con barcode, name y price, pero SIN description y SIN proveedor
- **THEN** el sistema retorna 200 y el producto se persiste con `description = NULL` y `proveedor = NULL`
- **AND** el sistema NO retorna 500

#### Scenario: Código de barras duplicado
- **WHEN** se envía POST /api/products/ con un barcode ya existente
- **THEN** el sistema retorna 400 con detalle "Ya existe un producto con ese codigo de barras"
- **AND** no se dispara ningún enriquecimiento en segundo plano

#### Scenario: Precio inválido
- **WHEN** se envía POST /api/products/ con price <= 0
- **THEN** el sistema retorna 400 con detalle "El precio del producto debe ser mayor que cero"

### Requirement: Atributos inferidos por IA al crear producto
El sistema SHALL extraer atributos del nombre y descripción del producto usando un modelo de IA (`attribute_extractor`), crear las categorías y atributos necesarios, y asociarlos al producto.

Este enriquecimiento SHALL ejecutarse **en segundo plano**, después de haber respondido el alta, en un hilo daemon con su propia sesión de base de datos.

El enriquecimiento SHALL usar **un solo modelo de IA por producto**: la máquina sostiene un único modelo Ollama residente, así que un segundo modelo en el mismo flujo expulsa al primero y lo obliga a recargar de disco. `create_categories` SHALL invocarse únicamente como fallback, cuando `attribute_extractor` no devuelva ningún atributo.

La categoría `proveedor` SHALL garantizarse determinísticamente, sin modelo: que la categoría de un proveedor se llama "proveedor" ya lo sabe el sistema.

El enriquecimiento SHALL ser el **mismo** para un producto creado por el formulario web y para uno creado por el chat del agente: una única implementación compartida, en la capa de servicios.

Un fallo del enriquecimiento NO SHALL afectar al alta: el producto ya está creado y la respuesta ya se emitió. El error SHALL registrarse y descartarse.

#### Scenario: Atributos inferidos y asignados
- **WHEN** se crea un producto con nombre y descripción
- **THEN** el sistema invoca `attribute_extractor` para extraer atributos
- **AND** crea las categorías y atributos que no existan
- **AND** asocia los atributos al producto mediante ProductAttribute

#### Scenario: Enriquecimiento en segundo plano
- **WHEN** se crea un producto vía POST /api/products/
- **THEN** la respuesta se emite sin esperar al enriquecimiento
- **AND** el enriquecimiento se ejecuta después en un hilo daemon
- **AND** los atributos quedan asociados al producto una vez que termina

#### Scenario: Un solo modelo cuando el extractor infiere atributos
- **WHEN** `attribute_extractor` devuelve al menos un atributo
- **THEN** el sistema NO invoca `create_categories`
- **AND** el enriquecimiento consume una sola invocación de modelo

#### Scenario: Fallback cuando el extractor no infiere nada
- **WHEN** `attribute_extractor` no devuelve ningún atributo
- **THEN** el sistema invoca `create_categories` para sembrar categorías para los próximos productos

#### Scenario: Atributos existentes asignados sin modelo
- **WHEN** el nombre o la descripción del producto mencionan un atributo que ya existe en la base
- **THEN** el sistema vincula el producto a ese atributo determinísticamente, sin invocar ningún modelo

#### Scenario: Fallo del enriquecimiento no afecta al alta
- **WHEN** el enriquecimiento en segundo plano falla (Ollama caído, modelo faltante)
- **THEN** el producto permanece creado y la respuesta del alta ya fue exitosa
- **AND** el error se registra sin propagarse

El valor del atributo `proveedor` SHALL ser **literalmente** el que el usuario escribió en el campo, normalizado (trim + minúsculas) y nada más. El sistema NO SHALL aceptar el valor de proveedor que devuelva un modelo, ni siquiera cuando el modelo lo devuelve: el proveedor es un dato explícito del usuario y el dato explícito prevalece sobre el modelo (requirement transversal "Preferir preguntar antes que especular"). Si el modelo emite un atributo de categoría `proveedor`, su valor SHALL sobrescribirse con el literal del usuario.

#### Scenario: Proveedor inferido desde campo dedicado
- **WHEN** se crea un producto con el campo proveedor informado
- **THEN** el sistema trata `proveedor` como una categoría de atributo del producto
- **AND** crea la categoría `proveedor` si no existe, determinísticamente y sin invocar ningún modelo
- **AND** crea u obtiene un atributo cuyo nombre sea el valor ingresado en el campo proveedor
- **AND** asocia ese atributo al producto mediante ProductAttribute

#### Scenario: El modelo deforma el proveedor
- **WHEN** se crea un producto con proveedor "arcor" y el modelo devuelve un atributo `proveedor` con valor "acro"
- **THEN** el sistema guarda el atributo `proveedor` con valor "arcor", el que escribió el usuario
- **AND** NO guarda "acro"

#### Scenario: Mismo proveedor en altas sucesivas
- **WHEN** se crean varios productos con el mismo proveedor "arcor"
- **THEN** todos quedan asociados al MISMO atributo `proveedor: arcor`
- **AND** no se crean variantes deformadas del nombre del proveedor

#### Scenario: Proveedor no informado
- **WHEN** se crea un producto sin proveedor válido
- **THEN** el sistema no crea la categoría `proveedor`
- **AND** no asocia atributos de proveedor al producto
