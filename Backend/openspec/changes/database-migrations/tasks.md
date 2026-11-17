# Tareas — Migraciones de base de datos con Alembic

> **No implementar hasta que estén resueltas las tareas de la sección 0.**
> La 0.1 es una decisión de gobernanza (Alembic figura como *gap* en la bóveda) y
> condiciona todo el resto.

## 0. Aprobaciones previas (bloqueantes)

- [x] 0.1 Aprobar la adopción de Alembic pese a figurar en `wiki/backend/SQLAlchemy.md` bajo "Gaps identificados" (o elegir la opción B de la Decisión 1: migrador propio con `PRAGMA user_version`)
- [x] 0.2 Resolver *Open Question 2*: ¿se mueve `Base` a `Backend/models/base.py` en este change o en uno propio?
- [x] 0.3 Resolver *Open Question 4*: ¿se crea infraestructura de tests (pytest) en este change o las pruebas 1–6 se corren a mano?
- [x] 0.4 Confirmar el nombre de la capacidad: `persistence`
- [x] 0.5 Confirmar la retención de backups (N=5)

## 1. Entorno Alembic

- [x] 1.1 Agregar `alembic` con versión fijada a `requirements.txt` (runtime, no build)
- [x] 1.2 Crear `Backend/alembic.ini` apuntando a `Backend/migrations` — **solo para el CLI en desarrollo**, no se empaqueta
- [x] 1.3 Crear `Backend/migrations/` con `env.py` y `script.py.mako`
- [x] 1.4 `env.py`: importar los 6 modelos **una sola vez** y exponer `Base.metadata` como `target_metadata`
- [x] 1.5 `env.py`: tomar la URL de `runtime.db_path()`, sin reutilizar el `engine` de `Backend/database.py`
- [x] 1.6 `env.py`: configurar `render_as_batch=True`, `compare_type=True` y `transaction_per_migration=True`
- [x] 1.7 Definir la `naming_convention` en `Base.metadata` para las restricciones **futuras** (Decisión 5)
- [x] 1.8 Agregar `Backend/migrations/versions/__pycache__/` y artefactos temporales a `.gitignore`

## 2. Revisión base

- [x] 2.1 Generar la revisión base y **editarla a mano** para que reproduzca el DDL real de 1.0.1, no lo que renderiza la convención de nombres nueva
- [x] 2.2 Verificar tabla por tabla contra el DDL relevado en `design.md` → *Estado real verificado del esquema*: 6 tablas, 7 índices, `uq_category_attribute`, la única sin nombre de `product_attributes`, `sales.state` como `VARCHAR(9)` sin `CHECK`
- [x] 2.3 Escribir el `downgrade()` de la revisión base
- [x] 2.4 Comprobar la equivalencia: aplicar la revisión base sobre una base vacía y comparar su DDL contra el DDL de 1.0.1 congelado en `Backend/tests/support.py` (la semilla se retiró en 6.2)
- [x] 2.5 Anotar como deuda la migración futura que le pone nombre a la restricción de `product_attributes` (NO se hace en este change)

## 3. Runner de migraciones

- [x] 3.1 Crear `Backend/migrations_runner.py` con la configuración programática de Alembic (`Config()` + `set_main_option`), sin leer `alembic.ini`
- [x] 3.2 Implementar la clasificación de la base (Decisión 3): casos A, B, C, D, E
- [x] 3.3 Caso C: antes de sellar, verificar que estén las 6 tablas esperadas; si falta alguna, abortar en vez de sellar
- [x] 3.4 Caso E: abortar sin escribir nada en el archivo, con el motivo en el log
- [x] 3.5 Implementar el respaldo previo (`sqlite3.Connection.backup()`, no `shutil.copy2()` sobre una base abierta) hacia `%LOCALAPPDATA%\EscanApp\backups\`
- [x] 3.6 Implementar la retención de las últimas N copias
- [x] 3.7 No respaldar si la base está vacía o si no hay nada pendiente
- [x] 3.8 Exponer una función que devuelva la revisión actual y si está en head (la usan el endpoint de estado y el log)
- [x] 3.9 Mensajes de error redactados para un dueño de kiosco: qué pasó, que **sus datos están intactos**, y dónde está el log

## 4. Reemplazo de `create_all()`

- [x] 4.1 `Backend/database.py`: `init_db()` deja de llamar a `Base.metadata.create_all()` y delega en el runner
- [x] 4.2 Verificar que `init_db()` sigue siendo invocado por `create_app()` **antes** de montar los routers
- [x] 4.3 Confirmar que ningún otro archivo del proyecto llama a `create_all()`
- [x] 4.4 Verificar que un fallo del runner llega a `fatal()` en `main.py` y muestra el `MessageBox` (la app corre con `console=False`)

## 5. Rutas y empaquetado

- [x] 5.1 `Backend/runtime.py`: agregar `migrations_dir()` resolviendo contra `resource_dir()`
- [x] 5.2 `Backend/runtime.py`: agregar `backups_dir()` resolviendo contra `data_dir()`
- [x] 5.3 `pos.spec`: agregar `Backend/migrations` a `data_entries()` con `raise SystemExit` si falta (igual que `Frontend/dist` y `Modelfiles`)
- [x] 5.4 `pos.spec`: agregar `collect_submodules("alembic")` y `"mako"` a `hidden`
- [ ] 5.5 Verificar que las rutas resuelven bien en onedir de PyInstaller 6.x (los datos quedan en `_internal/`, y `sys._MEIPASS` **sí** está definido; el comentario de `runtime.resource_dir()` dice lo contrario y quedó desactualizado)

## 6. Retiro de la semilla (Decisión 4)

- [x] 6.1 Quitar la entrada de `installer/seed/pos.db` de `data_entries()` en `pos.spec`
- [x] 6.2 Borrar `installer/seed/pos.db` del repositorio
- [x] 6.3 Quitar la excepción `!installer/seed/pos.db` de `.gitignore`
- [x] 6.4 **Conservar** `runtime.ensure_seed_database()` y `seed_db_path()` sin cambios (ya manejan la ausencia de semilla; quedan para el día que se envíen datos precargados)
- [x] 6.5 Actualizar el comentario de `ensure_seed_database()`: sin semilla, las tablas ahora las crea Alembic, no `create_all()`

## 7. Versión de esquema visible

- [x] 7.1 `Backend/api/app.py`: agregar `schema_revision` y `schema_is_head` a `/api/system/status`
- [x] 7.2 `main.py`: sumar la revisión de esquema al encabezado que `setup_logging()` escribe en cada arranque
- [x] 7.3 Registrar en el log qué hizo el runner: sellar, migrar de X a Y, o nada

## 8. Pruebas (los 8 escenarios de `design.md`)

- [x] 8.1 Instalación nueva: sin `pos.db` → 6 tablas + `alembic_version` en head
- [x] 8.2 **Instalación 1.0.x con datos**: sellada y migrada; **el conteo de filas de las 6 tablas no cambia**; existe la copia en `backups/`
- [x] 8.3 Arranque repetido: la segunda vez es no-op y no genera backup nuevo
- [x] 8.4 Base ajena (caso E): la app no arranca, no toca el archivo, el log explica por qué
- [x] 8.5 Equivalencia: el DDL de una instalación nueva es idéntico al de una migrada
- [x] 8.6 Sin deriva: `alembic revision --autogenerate` sobre una base en head produce una revisión **vacía**
- [ ] 8.7 Empaquetado: `build_release.bat` → instalar el `.exe` en una VM limpia → arranca, crea la base, registra una venta
- [ ] 8.8 **Actualización end-to-end**: instalar 1.0.1, cargar productos y una venta, instalar la versión nueva encima → los datos siguen ahí y `/api/system/status` reporta la revisión nueva
- [x] 8.9 Usar `ESCANAPP_DATA_DIR` para armar los escenarios 8.1–8.6 contra bases descartables

## 9. Documentación y gobernanza

- [x] 9.1 `docs/RELEASE.md`: agregar la sección "cómo escribir una migración" y la regla de que **ninguna versión se publica sin correr la prueba 8.8**
- [x] 9.2 `README.md`: mencionar el versionado del esquema en la sección de desarrollo
- [ ] 9.3 Actualizar `wiki/backend/SQLAlchemy.md` de la bóveda: mover Alembic de "Gaps identificados" a "Lo que sé hacer" y sumar este proyecto a "Proyectos donde lo usé"
- [ ] 9.4 `openspec/config.yaml`: registrar la capacidad `persistence` en la sección `specs` (queda para cuando se archive el change: hoy `specs/persistence/spec.md` todavía vive dentro de `changes/`)
- [x] 9.5 `openspec validate database-migrations`
