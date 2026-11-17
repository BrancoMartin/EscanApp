## Why

**Hoy el esquema de la base solo sabe crearse, no sabe evolucionar.** `Backend/database.py` usa `Base.metadata.create_all()`, que crea las tablas que faltan y **no toca las que ya existen**. Mientras la base era la del desarrollador esto no molestaba: se borraba `pos.db` y listo.

Con clientes pagos deja de ser una opción. El día que una versión agregue una columna (stock, medio de pago, la tabla de licencia), el kiosco que instale la actualización se queda con el esquema viejo, `create_all()` no dice nada, y la app rompe con `no such column` **con las ventas del negocio adentro**. Borrar `pos.db` para arreglarlo significa borrarle el inventario y el historial al cliente. Es el único problema de esta lista que **no se puede arreglar después**: una vez que hay bases en la calle sin control de versión, no hay forma de saber en qué estado está cada una.

Además hoy conviven **dos fuentes de verdad** del esquema: `create_all()` desde los modelos y el archivo semilla `installer/seed/pos.db` que el instalador copia. Nada garantiza que digan lo mismo.

## What Changes

- **Alembic pasa a ser el único mecanismo de evolución del esquema.** Se agrega `alembic` como dependencia de runtime (no solo de build: las migraciones corren en la PC del cliente).
- **BREAKING (interno):** `init_db()` deja de usar `Base.metadata.create_all()` para crear/evolucionar el esquema. La creación de tablas pasa a ser responsabilidad de la migración base. Ningún modelo, servicio ni endpoint cambia de comportamiento.
- **Migración base (baseline)** que reproduce exactamente el esquema actual de la versión 1.0.1: 6 tablas, sus índices y sus restricciones únicas.
- **Adopción de bases existentes sin pérdida de datos.** Una base de un cliente 1.0.x no tiene tabla `alembic_version`. Al detectarla, el sistema la **sella** (`stamp`) en la revisión base en vez de intentar recrear tablas que ya existen, y recién después aplica las migraciones nuevas.
- **Ejecución automática al arrancar**, antes de que cualquier sesión de SQLAlchemy toque la base. Si la migración falla, la app **no arranca a medias**: informa el error y deja los datos intactos.
- **Copia de seguridad previa obligatoria.** Antes de aplicar cualquier migración sobre una base con datos, el sistema SHALL copiar `pos.db`. Es la estrategia de rollback: una migración fallida se revierte restaurando la copia.
- **Versión de esquema consultable.** La revisión actual se expone en `/api/system/status` (junto a la versión del producto, que ya está ahí) y se escribe en el log de arranque, para poder diagnosticar por teléfono en qué estado está la instalación de un cliente.
- **Una sola fuente de verdad del esquema.** El `pos.db` semilla deja de definir el esquema: las migraciones lo crean. (Alternativa evaluada en `design.md`: seguir enviando la semilla, sellada en build.)
- **Soporte explícito de SQLite:** las migraciones SHALL usar el modo *batch* de Alembic, porque SQLite no soporta `ALTER TABLE DROP COLUMN` ni cambio de tipo, y sin batch cualquier migración futura que no sea "agregar columna" falla en la máquina del cliente.
- **Compatible con PyInstaller:** los scripts de migración viajan como recurso de solo lectura dentro del bundle y se localizan con `runtime.resource_dir()`, igual que `Frontend/dist` y los `Modelfiles`.

**Fuera de alcance (no se agrega nada de esto):** columnas nuevas, tablas nuevas, stock, medio de pago, cambios de modelo, backups programados, exportación de datos, ORM alternativo, migrar a otro motor de base.

## Capabilities

### Added Capabilities
- `persistence`: evolución versionada del esquema de la base de datos — creación en instalaciones nuevas, actualización sin pérdida de datos en instalaciones existentes, ejecución automática al arrancar, versión consultable y respaldo previo a migrar.

### Modified Capabilities
Ninguna. Este change no altera ningún requisito de `products`, `sales`, `categories`, `ai-agent`, `ui` ni `timestamps`: el esquema resultante es idéntico al actual.

## Impact

- **Dependencias:** `alembic` se suma a `requirements.txt` (runtime). Es la herramienta de migraciones del propio SQLAlchemy, que ya es la base del proyecto.
  - **Nota de gobernanza:** en la bóveda, `wiki/backend/SQLAlchemy.md` menciona Alembic en **"Gaps identificados"** (línea 43), no en "Lo que sé hacer". Está nombrado en la bóveda como la herramienta de migraciones de SQLAlchemy, pero adoptarlo **cierra un gap declarado**. Requiere tu confirmación explícita y actualizar esa nota al implementar.
- **Código afectado:**
  - `Backend/database.py` — `init_db()` deja de llamar a `create_all()` y pasa a delegar en el runner de migraciones.
  - `Backend/runtime.py` — dos rutas nuevas (carpeta de migraciones dentro de los recursos, carpeta de backups dentro de los datos del usuario).
  - `Backend/api/app.py` — `/api/system/status` reporta la revisión del esquema.
  - `pos.spec` — los scripts de migración se empaquetan como datos; `alembic` como import oculto.
  - `requirements.txt`, `.gitignore`.
- **Archivos nuevos:** `Backend/migrations/` (entorno Alembic + revisión base), `Backend/alembic.ini` (solo para el CLI en desarrollo), `Backend/migrations_runner.py` (el que decide sellar/migrar/no hacer nada).
- **Datos del cliente:** ninguna migración de este change modifica una sola fila. El esquema queda **byte a byte equivalente** al actual; lo único que se agrega a la base es la tabla `alembic_version`.
- **Instalador:** sin cambios en `EscanApp.iss`. La actualización in-place ya funciona por `AppId` fijo, y la migración corre en el primer arranque de la versión nueva, no durante la instalación (que corre elevada y no sabe a qué perfiles de usuario pertenecen las bases).
- **Desbloquea:** cualquier change posterior que toque el esquema — `licensing-system`, stock, medio de pago, cierre de caja. Este es el prerequisito de todos ellos.
