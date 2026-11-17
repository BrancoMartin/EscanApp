# database-integrity — Etapa 1: infraestructura y protección de datos

Branch: `commercial-readiness` · Delivery: `single-pr` (una etapa) · Test runner: `python -m pytest` (pytest 9.x, bases SQLite temporales)

## Specs

- **S1** Alembic es el único mecanismo de creación y evolución del esquema. Las bases nuevas se crean aplicando migraciones; `Base.metadata.create_all()` deja de usarse para crear o evolucionar el esquema.
- **S2** El esquema se define en los modelos SQLAlchemy. La revisión base reproduce el esquema 1.0.1: tablas `products`, `categories`, `attributes`, `product_attributes`, `sales`, `sale_items`; 7 índices; `CONSTRAINT uq_category_attribute UNIQUE (category_id, name)`; `UNIQUE (product_id, attribute_id)` sin nombre; `sales.state VARCHAR(9)` sin `CHECK`.
- **S3** Una base existente sin `alembic_version` se **sella** (`stamp`) en la revisión base y luego se migra. No se borra, recrea ni vacía. Productos, ventas, categorías y atributos se conservan sin alteración ni duplicación. La adopción ocurre una sola vez.
- **S4** La migración corre automáticamente al arrancar, en `init_db()`, antes de la primera sesión de negocio. Si falla, la app no arranca a medias e informa el error y que los datos están intactos.
- **S5** Una base que existe, no tiene registro de versión y no contiene las 6 tablas esperadas se considera desconocida: se aborta sin escribir nada y se registra el motivo.
- **S6** Antes de migrar una base con datos se crea un backup verificable en la carpeta de datos del usuario (`%LOCALAPPDATA%\EscanApp\backups`), usando la API de backup de SQLite (no `shutil.copy2` sobre una base abierta). No se respalda si no hay nada pendiente o la base está vacía.
- **S7** Backups automáticos con política configurable: retención de las últimas 5 copias por defecto, sin sobrescribir backups válidos, con registro de fecha, versión del producto, revisión de esquema y resultado. Cada backup se verifica abriéndolo y leyéndolo.
- **S8** Restauración de backups: permite seleccionar una copia, valida integridad, protege la base actual antes de reemplazarla, se niega si hay operaciones activas y deja un estado consistente ante errores, informando el resultado.
- **S9** pytest instalado y configurado con bases SQLite temporales y fixtures reutilizables; la suite se ejecuta desde la raíz. Ningún test usa `pos.db` real ni datos reales.
- **S10** Tests de productos (alta, consulta, actualización, validación de código de barras, integridad), ventas (registro, cálculo, persistencia, relaciones), base de datos (inicialización, migraciones, backups, restauración, recuperación) y actualización entre versiones (base 1.0.1 con datos representativos → datos intactos y esquema final correcto).
- **S11** `installer/seed/pos.db` deja de ser fuente de verdad del esquema y se retira del repositorio y del empaquetado. No contiene datos iniciales (0 filas), por lo que no hay datos que preservar.
- **S12** Empaquetado compatible con PyInstaller: `Backend/migrations` viaja como dato y el build se detiene si falta.
- **S13** `/api/system/status` expone `schema_revision` y `schema_is_head`; el arranque registra la revisión en el log.
- **S14** No se modifican reglas comerciales, `installer/EscanApp.iss` ni la identidad del instalador. No se agregan tecnologías fuera de `alembic` (runtime) y `pytest` (desarrollo).

## Tasks

- T1 (S1, S2, S14) `Backend/models/base.py` + modelos + `database.py` sin `create_all` → inline — **done**
- T2 (S1, S2) `Backend/migrations/` (env, template, revisión base) + `Backend/alembic.ini` → inline — **done**
- T3 (S3, S4, S5, S6) `Backend/migrations_runner.py` con clasificación A–E y backup previo → inline — **done**
- T4 (S6, S7) `Backend/database_backup.py` (backup, manifiesto, retención, política) → inline — **done**
- T5 (S8) `Backend/database_restore.py` + `Backend/db_lock.py` + CLI → inline — **done**
- T6 (S12, S13) `runtime.py`, `app.py`, `main.py`, `pos.spec` → inline — **done**
- T7 (S11) retiro de `installer/seed/pos.db`, `.gitignore` → inline — **done**
- T8 (S9, S10) `pytest.ini`, `requirements-dev.txt`, `Backend/tests/` → inline — **done** (52 tests)
- T9 (S13, S14) docs + OpenSpec → inline — **done** (queda 9.3 bóveda y 9.4 al archivar)
- T10 verificación: suite completa, drift `compare_metadata`, equivalencia de esquema → inline — **done**

## Log

- L1 (prompt original, verbatim resumido por longitud): "PROMPT 1 — ETAPA 1: INFRAESTRUCTURA Y PROTECCIÓN DE DATOS … implementar la primera etapa de profesionalización de EscanApp: garantizar la integridad, persistencia, recuperación y evolución segura de los datos." Objetivos: Alembic, eliminar dependencia de seed/pos.db, migrar bases existentes sin perder información, backups automáticos (últimas 5), restauración, pytest y tests. No avanzar a la etapa 2.
- L2 Decisión: el change OpenSpec existente `Backend/openspec/changes/database-migrations/` resuelve las aprobaciones pendientes: Alembic aprobado por el pedido, N=5 confirmado, pytest incluido en esta etapa. `Base` se mueve a `Backend/models/base.py` para que `env.py` no dispare `ensure_user_data()` ni cree el engine.
- L3 Evidencia: DDL de `installer/seed/pos.db` y `pos.db` verificados con `sqlite_master`; coinciden exactamente con el relevado en `design.md`. La semilla está vacía (0 filas).
- L4 Hallazgo y corrección (S9): `runtime.seed_db_path()` resolvía en desarrollo a `<repo>/pos.db` —la base de trabajo con datos reales—, así que cualquier arranque con `ESCANAPP_DATA_DIR` copiaba esa base a la carpeta descartable (y una instalación "nueva" se clasificaba como caso C). Ahora en desarrollo busca `installer/seed/pos.db` (retirada) y solo el bundle usa `<bundle>/pos.db`. Test de regresión en `Backend/tests/test_runtime.py`.
- L5 Verificación: `python -m pytest` → 52 passed. Deriva `compare_metadata` con `include_object` → `[]`. Equivalencia DDL instalación nueva vs 1.0.1 congelado → idéntica (tablas, columnas, índices, FKs). Humo `create_app()` con `ESCANAPP_DATA_DIR` temporal → caso A, revisión `0001_initial_schema`, `schema_is_head: true`.
- L6 Pendiente fuera de alcance: T8.7/T8.8 del change OpenSpec (build real + actualización end-to-end en VM) y 9.3/9.4 de gobernanza. `SaleService.create()` sigue siendo código muerto preexistente; no se tocó.
