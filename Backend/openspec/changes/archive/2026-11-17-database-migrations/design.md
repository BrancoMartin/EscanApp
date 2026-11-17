# Diseño técnico — Migraciones de base de datos con Alembic

## Context

### Cómo se crea hoy el esquema

`Backend/database.py` hace tres cosas **en el momento del import**, antes de que nadie llame a nada:

```python
runtime.ensure_user_data()            # siembra pos.db y Modelfiles si es el primer arranque
BASE_DIR = runtime.data_dir()
DATABASE_URL = f"sqlite:///{runtime.db_path()}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

y expone `init_db()`, que importa los 6 modelos y llama a `Base.metadata.create_all(bind=engine)`. `init_db()` se invoca una sola vez, desde `create_app()` en `Backend/api/app.py`, que corre dentro del hilo del servidor lanzado por `main.py`.

`create_all()` emite `CREATE TABLE IF NOT EXISTS` por tabla. **Sobre una tabla que ya existe no hace absolutamente nada**: no compara columnas, no avisa de diferencias, no falla. Es correcto para crear, y es exactamente lo que no sirve para evolucionar.

### Las dos fuentes de verdad

El esquema hoy puede nacer por dos caminos distintos:

| Camino | Quién lo produce | Cuándo |
|---|---|---|
| `installer/seed/pos.db` | archivo binario versionado en git, copiado por `runtime.ensure_seed_database()` | primer arranque de cada usuario, si el archivo semilla existe en el bundle |
| `Base.metadata.create_all()` | los modelos SQLAlchemy | siempre, después de lo anterior |

Nada verifica que los dos coincidan. Hoy coinciden —lo comprobé, ver abajo— pero por disciplina del desarrollador, no por construcción. Si alguien agrega una columna a un modelo y no regenera la semilla, las instalaciones nuevas quedan con un esquema y `create_all()` no lo nota.

### Estado real verificado del esquema (v1.0.1)

Comparé el DDL de `installer/seed/pos.db` y del `pos.db` de desarrollo. **Son idénticos entre sí y consistentes con los modelos.** Ese es el punto de partida que tiene que reproducir la migración base:

- **6 tablas:** `products`, `categories`, `attributes`, `product_attributes`, `sales`, `sale_items`.
- **Índices:** `ix_products_id`, `ix_products_name`, `ix_products_barcode` (UNIQUE), `ix_categories_name` (UNIQUE), `ix_attributes_id`, `ix_sales_id`, `ix_sale_items_id`.
- **Restricciones únicas con nombre:** `uq_category_attribute` en `attributes (category_id, name)`.
- **Restricciones únicas SIN nombre:** `product_attributes (product_id, attribute_id)` → SQLite la materializa como `sqlite_autoindex_product_attributes_1`. Esto tiene consecuencias (Decisión 5).
- **`sales.state`** es `VARCHAR(9)` sin `CHECK`: es un `Enum` de SQLAlchemy con `create_constraint=False` (el default desde 1.4).
- **`PRAGMA user_version` = 0** en ambas bases, y **no existe** ninguna tabla de versión. No hay ningún rastro de versionado de esquema en la base: nada que reutilizar, nada que respetar.
- La semilla está **vacía de datos** (0 filas en las 6 tablas). Es solo esquema.

### Restricciones del entorno

1. **SQLite.** No soporta `DROP COLUMN` ni `ALTER COLUMN`. La única forma de hacer eso es recrear la tabla, copiar los datos y renombrar.
2. **PyInstaller onedir.** `pos.spec` empaqueta módulos por import y recursos por `datas`. Los scripts de migración de Alembic **no se importan**: Alembic los carga por ruta en tiempo de ejecución. PyInstaller no los va a ver.
3. **Dos raíces distintas.** `runtime.resource_dir()` (solo lectura, dentro del bundle) vs `runtime.data_dir()` (`%LOCALAPPDATA%\EscanApp`, escribible). Las migraciones son recurso; la base y los backups son datos.
4. **Sin consola.** El `.exe` corre con `console=False`. Un error de migración por `stderr` no lo ve nadie: tiene que ir al log y al cuadro de diálogo de `fatal()` que ya existe en `main.py`.
5. **Sin conexión garantizada.** La migración corre en la PC del kiosco, offline, sin nadie que sepa qué es una base de datos.

## Goals / Non-Goals

**Goals:**

- Que el esquema tenga **una sola fuente de verdad versionada** y que cada instalación diga en qué versión está.
- Que una instalación 1.0.x con datos reales se actualice a 1.1 **sin perder una fila**.
- Que una instalación nueva quede en el mismo estado que una migrada.
- Que todo eso ocurra **solo**, al arrancar, sin que el usuario del kiosco haga nada.
- Que funcione igual en `python main.py` y en `EscanApp.exe`.
- Que exista un camino de vuelta si una migración sale mal.

**Non-Goals:**

- Cambiar el esquema. Este change no agrega ni saca una columna. El resultado es el esquema actual, versionado.
- Migrar a otro motor de base (PostgreSQL, MySQL). Sigue siendo SQLite.
- Backups programados, retención, exportación o restauración desde la UI. Lo único que se implementa es la **copia previa a migrar**, porque es el rollback de esta capacidad.
- Multi-tenant, sincronización o base remota.
- Migraciones de datos (transformar filas). El mecanismo las va a soportar; este change no escribe ninguna.

## Decisions

### Decisión 1 — Alembic, no un migrador propio

**Opciones**

| Opción | Cómo versiona | Costo | Riesgo |
|---|---|---|---|
| (A) Seguir con `create_all()` | no versiona | cero | pérdida de datos en el cliente, irreversible |
| (B) Migrador propio con `PRAGMA user_version` | entero incremental + `if` por versión | ~150 líneas propias | todo el trabajo de recrear tablas en SQLite queda a mano; sin autogenerate; sin downgrade |
| (C) **Alembic** | tabla `alembic_version` con hash de revisión | dependencia nueva (~1 MB) | curva de aprendizaje; empaquetado en PyInstaller |

**Elegida: (C).** Alembic es la herramienta de migraciones del propio SQLAlchemy, que ya es el ORM del proyecto: no introduce un modelo mental nuevo, `op.add_column()` habla el mismo idioma que `Column()`. Trae resuelto lo que en (B) habría que escribir a mano y bien: el modo *batch* para SQLite (Decisión 5), la detección de deriva con `--autogenerate`, y el grafo de revisiones con `downgrade`.

(B) es tentador por lo chico del proyecto, pero el trabajo real de una migración en SQLite no es llevar el contador de versión —eso son 10 líneas— sino recrear tablas preservando datos, índices y restricciones. Eso es exactamente lo que Alembic ya hace.

> **Gobernanza (`openspec/config.yaml`):** la bóveda nombra a Alembic en `wiki/backend/SQLAlchemy.md`, pero bajo **"Gaps identificados"** (línea 43: *"Alembic para migraciones de base de datos"*), no bajo "Lo que sé hacer". No es tecnología ajena a la bóveda —está declarada como el siguiente paso natural de SQLAlchemy— pero **adoptarla cierra un gap abierto**, y eso requiere tu aprobación explícita antes de implementar. Ver *Open Questions*.

### Decisión 2 — La migración corre al arrancar, antes de la primera sesión

**Dónde exactamente:** `init_db()` en `Backend/database.py` deja de llamar a `create_all()` y pasa a llamar al runner de migraciones. `create_app()` la sigue invocando en el mismo lugar de siempre.

**Por qué ahí y no antes:** la tentación es correrla al importar `Backend.database`, junto a `ensure_user_data()`. Es mala idea: el import ocurre también cuando lo hace el `env.py` de Alembic (para leer `Base.metadata`), y quedaría migrando la base como efecto secundario de generar una revisión. `init_db()` es un punto explícito, ya existente, y garantizado antes del primer `SessionLocal()` porque `create_app()` lo llama antes de montar los routers.

**Por qué no en el instalador:** `EscanApp.iss` corre elevado y una sola vez por máquina. La base es **por usuario** (`%LOCALAPPDATA%`). El instalador no sabe a qué perfiles migrarles la base — es el mismo razonamiento que ya está escrito en `runtime.ensure_seed_database()`.

**Si falla:** el runner propaga la excepción. `create_app()` muere, el servidor no levanta, `wait_server()` de `main.py` da timeout y dispara `fatal()`, que muestra el `MessageBox` con la ruta del log. La app **no arranca a medias con el esquema roto**, y la base queda como estaba (Decisión 6). El mensaje tiene que decirle al usuario que llame a soporte y **que sus datos están intactos**.

### Decisión 3 — Las bases existentes se *sellan*, no se migran desde cero

Es la decisión central de este change. La migración base contiene `CREATE TABLE products ...`. Si se la aplicáramos a la base de un cliente 1.0.x, que ya tiene `products`, fallaría con `table products already exists`.

Alembic resuelve esto con `stamp`: escribir la revisión en `alembic_version` **sin ejecutar la migración**, declarando "esta base ya está en este estado". El runner clasifica la base al arrancar:

| # | Estado detectado | Acción | Caso real |
|---|---|---|---|
| A | el archivo `pos.db` no existe | crear + `upgrade head` | instalación nueva |
| B | existe y tiene `alembic_version` | `upgrade head` (no-op si ya está en head) | instalación ya adoptada |
| C | existe, sin `alembic_version`, **con** tabla `products` | `stamp <base>` y después `upgrade head` | **cliente 1.0.x que actualiza** |
| D | existe, sin `alembic_version`, sin ninguna tabla | `upgrade head` | archivo vacío o creado a mano |
| E | existe, sin `alembic_version`, con tablas pero **sin** `products` | **abortar sin tocar nada** | base ajena, corrupta o de otro producto |

El caso E es el que hace cumplir el requisito de "nada destructivo sin migración explícita": ante una base que no reconoce, el sistema no adivina — se niega a operar y lo reporta.

El caso C es de un solo uso por instalación: después del `stamp`, esa base entra para siempre en el caso B.

**Alternativa descartada:** una migración base "idempotente" con `CREATE TABLE IF NOT EXISTS`. Suena más simple y es peor: haría que una base con esquema *parcialmente* distinto pase por buena, que es precisamente el bug que este change viene a eliminar.

### Decisión 4 — El `pos.db` semilla deja de definir el esquema

Con migraciones, la semilla es la segunda fuente de verdad que sobra. Dos opciones:

| Opción | Cómo | Contra |
|---|---|---|
| (A) **Retirar la semilla.** Las migraciones crean el esquema en el primer arranque (caso A) | borrar `installer/seed/pos.db`, su excepción en `.gitignore` y su entrada en `pos.spec` | el primer arranque paga ~6 `CREATE TABLE` (milisegundos) |
| (B) Mantenerla, sellada en build | `build_release.ps1` regenera la semilla corriendo `upgrade head` sobre un archivo nuevo | un paso más de build; sigue habiendo un binario en git |

**Elegida: (A).** El único servicio que prestaba la semilla era traer el esquema hecho, y ahora lo trae la migración base — de la misma fuente de la que sale todo lo demás. Retirarla elimina el binario versionado en git y el riesgo de que se desincronice.

`runtime.ensure_seed_database()` y `runtime.seed_db_path()` **se conservan tal cual**: ya manejan el caso de que no exista semilla (`return False`, y el comentario dice literalmente *"Sin semilla: SQLAlchemy creará las tablas vacías"* — pasa a ser Alembic). Quedan disponibles para el día que quieras enviar una base con datos precargados (un catálogo inicial de kiosco, por ejemplo). No se borra código que funciona.

### Decisión 5 — Modo *batch* y convención de nombres, por SQLite

**Batch.** `env.py` SHALL configurar `render_as_batch=True`. Sin eso, la primera migración que no sea "agregar columna" —quitar una columna, cambiar un tipo, agregar un `CHECK`— falla en la PC del cliente con un error de sintaxis de SQLite. Con batch, Alembic hace el baile completo: tabla temporal, copia de datos, drop, rename.

**Convención de nombres.** Batch recrea la tabla, y para recrearla necesita poder **nombrar** cada restricción. Y acá está el detalle que encontré en la auditoría: `product_attributes` tiene una `UniqueConstraint("product_id", "attribute_id")` **sin nombre**, que SQLite guardó como `sqlite_autoindex_product_attributes_1`. Una migración futura en batch sobre esa tabla se va a topar con eso.

La solución estándar es agregar una `naming_convention` a `Base.metadata`. **Pero tiene un efecto colateral que hay que manejar con cuidado:** al agregar la convención, SQLAlchemy empieza a *renderizar* nombres para restricciones que en la base real no los tienen, y `--autogenerate` va a proponer migraciones que "arreglan" nombres. Por eso:

1. La **migración base se escribe reproduciendo el DDL real que existe hoy** (unnamed donde hoy está unnamed), no lo que la convención nueva renderizaría. La base de un cliente sellada en esa revisión tiene que coincidir con lo que la revisión dice.
2. La convención de nombres se aplica **desde ahí en adelante**, para las restricciones nuevas.
3. Renombrar la restricción de `product_attributes` para alinearla es una **migración explícita, propia y posterior** — no un efecto secundario de este change. Queda anotada como deuda.

Además, `env.py` SHALL usar `compare_type=True` (SQLite guarda tipos laxos; sin esto, autogenerate no ve cambios de tipo) y `transaction_per_migration=True` (cada revisión en su propia transacción: si la tercera de cinco falla, las dos primeras quedan aplicadas y registradas, no en un limbo).

### Decisión 6 — Copia de seguridad antes de migrar, y es el rollback

Antes de aplicar una migración sobre una base que **tiene datos**, el runner copia `pos.db` a `%LOCALAPPDATA%\EscanApp\backups\pos-<revisión_actual>-<timestamp>.db`.

- No se copia si la base está vacía o si no hay nada que aplicar (caso B ya en head): no tiene sentido llenar el disco de copias idénticas en cada arranque.
- La copia se hace **con la base cerrada** o vía la API `sqlite3.Connection.backup()`, no con un `shutil.copy2()` a ciegas sobre una base abierta.
- Se conservan las últimas N (proponer N=5) y se borran las más viejas, para que 30 actualizaciones no dejen 30 copias de una base de 200 MB.

**Rollback:** restaurar la copia. La secuencia de recuperación de un cliente es: cerrar la app → reemplazar `pos.db` por la copia previa → reinstalar la versión anterior del `.exe`. Vuelve a estar donde estaba, con sus datos.

**Por qué la copia y no el `downgrade`:** `downgrade` existe y se va a escribir en cada revisión, pero en SQLite un downgrade que revierte un `DROP COLUMN` **no puede devolver los datos de esa columna**. El downgrade sirve en desarrollo, para ir y volver mientras iterás. El respaldo real del cliente es el archivo.

### Decisión 7 — PyInstaller: las migraciones son un recurso, no un módulo

Alembic localiza sus revisiones por **ruta de directorio** (`script_location`) y las carga con `exec` desde el archivo. PyInstaller sigue imports, no rutas: sin ayuda, `Backend/migrations/versions/*.py` no entra al bundle y el `.exe` arranca y falla con *"Path doesn't exist"* — **un error que no se manifiesta jamás en desarrollo**. Es el modo más probable de que este change se rompa.

El diseño:

1. `pos.spec` agrega `(Backend/migrations, "Backend/migrations")` a `data_entries()`, con la misma verificación `raise SystemExit` que ya usan `Frontend/dist` y `Modelfiles`: **si la carpeta no está, el build se detiene**. Un release sin migraciones no debe poder construirse.
2. `runtime.py` gana `migrations_dir()`, que resuelve `os.path.join(resource_dir(), "Backend", "migrations")` — congelado y en desarrollo, igual que `Frontend/dist`.
3. **En runtime no se lee `alembic.ini`.** La configuración se arma en memoria: `Config()` + `set_main_option("script_location", runtime.migrations_dir())` + `set_main_option("sqlalchemy.url", ...)`. Así no hay que empaquetar el `.ini` ni preocuparse por rutas relativas dentro del bundle.
4. `Backend/alembic.ini` **sí existe en el repo**, apuntando a `Backend/migrations`, exclusivamente para poder correr `alembic revision --autogenerate` y `alembic history` a mano en desarrollo.
5. `pos.spec` suma `collect_submodules("alembic")` a `hidden` (Alembic resuelve el dialecto `alembic.ddl.sqlite` dinámicamente) y `"mako"` (el motor de plantillas que Alembic importa desde `ScriptDirectory`).
6. El template `script.py.mako` viaja dentro de `Backend/migrations/` — solo hace falta para *generar* revisiones, pero va en el mismo directorio y no cuesta nada.

### Decisión 8 — La versión del esquema se expone donde ya se mira

`/api/system/status` ya devuelve `version` y `data_dir`. Se le agregan dos campos: `schema_revision` (lo que dice `alembic_version` de esa base) y `schema_is_head` (booleano). Y `main.py` ya escribe un encabezado en el log de cada arranque con versión y carpeta de datos: se le suma la revisión del esquema.

Con eso, diagnosticar a un cliente por teléfono es pedirle el log o abrir `/api/system/status`. Sin eso, no hay forma de saber en qué estado está una instalación remota — que es el requisito 5.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| **Las migraciones no entran al bundle y solo se rompe en el cliente.** El modo de falla más probable de todo el change. | `pos.spec` aborta el build si falta la carpeta (Decisión 7.1) + prueba obligatoria sobre el `.exe` construido, no solo en desarrollo (ver Plan de pruebas). |
| **El `stamp` se aplica a una base que NO corresponde a la revisión base** (un cliente con un `pos.db` tocado a mano). Quedaría marcada como al día siendo otra cosa, y la migración siguiente falla raro. | El caso E aborta ante bases desconocidas. Además, antes del `stamp`, verificar que existan las 6 tablas esperadas; si falta alguna, abortar y reportar en vez de sellar. |
| **`env.py` importa `Backend.database` y dispara efectos secundarios** (`ensure_user_data()`, creación del engine) con solo generar una revisión. | `env.py` importa `Base` y los modelos, y toma la URL de `runtime.db_path()`; no reutiliza el `engine` del módulo. Alternativa más limpia si molesta: mover `Base` a `Backend/models/base.py`, sin efectos secundarios. Ver *Open Questions*. |
| **Dos instancias de la app arrancando a la vez** (doble clic impaciente) migrando la misma base. | SQLite serializa por lock de archivo: la segunda espera o falla con *database is locked*. `transaction_per_migration` evita el estado intermedio. Se puede endurecer con un lock de archivo en `data_dir()` si aparece en las pruebas. |
| **Migración lenta sobre una base grande** (batch copia la tabla entera): la ventana de PyWebView tarda en abrir y el usuario cree que se colgó. | Con los volúmenes de un kiosco (miles de filas) es instantáneo. Si alguna vez deja de serlo, la app ya tiene el patrón para esto: `/api/system/status` + el aviso de "preparando los agentes" del frontend. Fuera de alcance por ahora. |
| **La restricción sin nombre de `product_attributes` complica una migración futura en batch.** | Documentada arriba; se resuelve con una migración explícita propia, no acá. |
| **`extend_existing=True` en `Category` y `ProductAttribute`** enmascara importaciones dobles de modelos y puede dar metadata inconsistente al autogenerate. | Verificar durante la implementación que `env.py` importe los modelos **una sola vez** y que el autogenerate sobre una base al día produzca una revisión **vacía**. Es la prueba de que la metadata coincide con la realidad. |
| **Alembic está declarado como gap en la bóveda.** | Aprobación explícita tuya + actualizar `wiki/backend/SQLAlchemy.md` al implementar (mover de "Gaps" a "Lo que sé hacer", con este proyecto en "Proyectos donde lo usé"). |
| **Los backups ocupan disco** en una PC de kiosco. | Retención de las últimas N (N=5) y solo se crea copia cuando de verdad se va a migrar una base con datos. |

## Migration Plan

**Orden de implementación** (el detalle operativo está en `tasks.md`):

1. Agregar `alembic` a `requirements.txt` y crear el entorno (`alembic.ini`, `migrations/env.py` con batch + convención).
2. Escribir la **revisión base** que reproduce el esquema 1.0.1 exacto, y verificarla contra el DDL real relevado en *Context*.
3. Escribir el runner con la clasificación A–E y el respaldo previo.
4. Reemplazar `create_all()` en `init_db()`.
5. Empaquetado: `pos.spec` (datas + hiddenimports), `runtime.migrations_dir()`, retiro de la semilla.
6. Exponer la revisión en `/api/system/status` y en el log.
7. Pruebas (abajo), incluidas las del `.exe` construido.

**Despliegue al cliente:** ninguna acción especial. Se publica la versión nueva como cualquier otra (`VERSION` + `build_release.bat`); el instalador actualiza in-place por `AppId` fijo, y la migración corre sola en el primer arranque. El cliente no ve nada, salvo un arranque un poco más lento esa única vez.

**Rollback (por orden de preferencia):**

1. **Nada que revertir.** Si la migración falla, falla dentro de su transacción: la base queda como estaba y la app no arranca. Se restaura el `.exe` anterior y el cliente sigue trabajando.
2. **Restaurar la copia previa** de `%LOCALAPPDATA%\EscanApp\backups\` sobre `pos.db`, con la app cerrada, y reinstalar la versión anterior.
3. **`alembic downgrade`** — solo desarrollo. En SQLite no devuelve datos que una migración haya borrado; no es el rollback del cliente.
4. **Rollback del change entero**, si se decide abortar la adopción: volver a `create_all()` en `init_db()`. Las bases ya selladas quedan con una tabla `alembic_version` de más, inerte, que `create_all()` ignora. No hay daño.

## Plan de pruebas

Lo que hay que probar no es Alembic —eso ya está probado— sino **la clasificación de la base y el empaquetado**. Los tres escenarios que importan:

| # | Escenario | Se arma así | Se espera |
|---|---|---|---|
| 1 | **Instalación nueva** | borrar `pos.db`, arrancar | 6 tablas + `alembic_version` en head; DDL idéntico al relevado |
| 2 | **Instalación 1.0.x con datos** (el crítico) | copia de un `pos.db` real con productos y ventas, sin `alembic_version` | sellada en base y llevada a head; **el conteo de filas de las 6 tablas no cambia**; existe la copia en `backups/` |
| 3 | **Arranque repetido** | arrancar dos veces seguidas | la segunda es no-op; no se crea un backup nuevo |
| 4 | **Base ajena** (caso E) | base con una tabla `foo` y nada más | la app **no arranca**, no modifica el archivo, el log dice por qué |
| 5 | **Equivalencia** | comparar DDL de (1) contra (2) | idénticos: una instalación nueva y una migrada son indistinguibles |
| 6 | **Sin deriva** | `alembic revision --autogenerate` sobre una base en head | la revisión generada sale **vacía** (prueba de que modelos y migraciones dicen lo mismo) |
| 7 | **Empaquetado** | `build_release.bat` → instalar el `.exe` en una VM limpia | arranca, crea la base, registra una venta |
| 8 | **Actualización real end-to-end** | instalar 1.0.1, cargar productos y una venta, instalar encima la versión nueva | los productos y la venta **siguen ahí**, `/api/system/status` reporta la revisión nueva |

Los escenarios 7 y 8 son los que no se pueden automatizar y son los que de verdad protegen al cliente: **ninguna versión se publica sin correr el 8**. `ESCANAPP_DATA_DIR` (que `runtime.data_dir()` ya soporta) permite armar los escenarios 1–6 contra bases descartables sin tocar la real.

## Open Questions

1. **Aprobación de Alembic.** Está en la bóveda como gap, no como conocimiento adquirido. ¿Se adopta y se actualiza `wiki/backend/SQLAlchemy.md`, o preferís el migrador propio con `PRAGMA user_version` (Decisión 1, opción B)?
2. **`Base` con efectos secundarios.** ¿Se mueve `Base` a `Backend/models/base.py` para que importar los modelos no dispare `ensure_user_data()` ni cree el engine? Es más limpio, pero toca el import de los 6 modelos y de `database.py` — decidir si entra en este change o va en uno propio.
3. **Retención de backups.** N=5 propuesto. ¿Sirve, o preferís conservar todos y que el cliente los borre?
4. **Infraestructura de tests.** El proyecto **no tiene ni un test ni pytest instalado** (`config.yaml` dice *"pytest (verify before creating)"* — verificado: no hay). Los escenarios 1–6 son automatizables. ¿Se crea `requirements-dev.txt` con pytest y el primer `Backend/tests/` en este change, o las pruebas se corren a mano acá y la infraestructura se arma en un change propio?
5. **Nombre de la capacidad.** Propuse `persistence`. ¿O preferís `database` / `esquema`?
