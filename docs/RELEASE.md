# Publicar una versión de EscanApp

## Resumen

```
1. Editar el archivo VERSION      (por ejemplo: 1.0.1)
2. Doble clic en scripts\build_release.bat
3. Subir release\EscanAppSetup.exe
```

Eso es todo. El script hace el resto.

---

## Qué necesitás instalado (solo vos, una vez)

| Herramienta | Para qué | Dónde |
|---|---|---|
| **Python 3.11+** | empaquetar el backend | https://www.python.org/downloads/ (marcá *Add python.exe to PATH*) |
| **Node.js LTS** | compilar el frontend React | https://nodejs.org/ |
| **Inno Setup 6** | generar el instalador | https://jrsoftware.org/isdl.php |

Si falta alguna, `build_release.bat` te lo dice con el link y se detiene. **Nunca** genera un instalador a medias.

El **cliente final no necesita nada de esto.**

---

## Qué hace `build_release.bat`

| Paso | Acción |
|---|---|
| 1 | Verifica Python, Node e Inno Setup |
| 2 | Borra `build/`, `dist/` y `Frontend/dist` de builds anteriores |
| 3 | `pip install -r requirements-build.txt` y `npm ci` |
| 4 | `npm run build` → `Frontend/dist` |
| 5 | `PyInstaller pos.spec` → `dist/EscanApp/` |
| 6 | `ISCC` → `release/EscanAppSetup-<versión>.exe` |

Deja dos archivos en `release/`:

- `EscanAppSetup-1.0.1.exe` — el artefacto versionado (para archivar).
- `EscanAppSetup.exe` — copia con nombre fijo (la que publicás para descargar).

Opciones para iterar más rápido durante el desarrollo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -SkipFrontend
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -SkipDeps
```

---

## Versionado

`VERSION` en la raíz es **la única fuente de verdad**. De ahí sale:

- el recurso de versión del `EscanApp.exe` (lo que muestra *Propiedades* en Windows),
- la versión que aparece en *Agregar o quitar programas*,
- el nombre del instalador,
- lo que devuelve `GET /api/system/status`.

Formato `MAJOR.MINOR.PATCH`:

| Cambio | Ejemplo |
|---|---|
| Arreglaste un bug | `1.0.0` → `1.0.1` |
| Agregaste una funcionalidad | `1.0.1` → `1.1.0` |
| Cambio grande / incompatible | `1.1.0` → `2.0.0` |

### Actualizaciones

El `AppId` del instalador (`installer/EscanApp.iss`) es un GUID fijo que **nunca** hay que cambiar. Gracias a eso, instalar la 1.1.0 sobre la 1.0.0 es una **actualización in-place**:

- no aparece una segunda entrada en *Agregar o quitar programas*,
- **la base de datos del usuario se conserva** (vive en `%LOCALAPPDATA%\EscanApp`, fuera de la carpeta de instalación),
- los modelos de IA ya creados no se vuelven a descargar.

Si cambiás el `AppId`, rompés todo eso. No lo toques.

### Migraciones de esquema (obligatorio desde 1.0.2)

El esquema de la base **no** se crea con `create_all()`: lo administra Alembic. Al arrancar,
`Backend/migrations_runner.py`:

1. clasifica la base —nueva, ya versionada, 1.0.x (tiene las 6 tablas pero no `alembic_version`),
   vacía o **desconocida**—;
2. si hay datos y hace falta cambiar el esquema, crea una copia verificada en `backups/`;
3. sella la base 1.0.x en la revisión base, aplica las migraciones pendientes y verifica que quedó
   en la última revisión.

Una base **desconocida** (archivo que no es SQLite, o tablas que no son las de EscanApp) **no se
modifica**: la aplicación no arranca, muestra el motivo real y el log indica la ruta del archivo.
No se adivina nunca.

Cómo escribir una migración:

```bash
cd Backend
alembic revision --autogenerate -m "descripcion corta"
# revisar el archivo generado en Backend/migrations/versions/ ANTES de commitear
alembic upgrade head
```

Reglas:

- Todo cambio de esquema va en una migración versionada. `create_all()` ya no se usa.
- Revisar a mano lo autogenerado: puede proponer renombres que en SQLite requieren
  `render_as_batch` y no son lo que querés. La restricción sin nombre de `product_attributes` está
  filtrada a propósito en `Backend/db_autogen.py` (deuda documentada).
- La migración debe funcionar en una **instalación nueva** y en una **actualización** desde 1.0.x
  con datos.
- Probar con `ESCANAPP_DATA_DIR` apuntando a un directorio temporal, nunca contra `pos.db` real:

```bash
set ESCANAPP_DATA_DIR=%TEMP%\escanapp-prueba
python -m pytest
```

- **Ninguna versión se publica sin correr la prueba de actualización end-to-end** (8.8 en
  `Backend/openspec/changes/database-migrations/tasks.md`): instalar 1.0.1, cargar productos y una
  venta, instalar la versión nueva encima y verificar que los datos siguen ahí y que
  `/api/system/status` reporta la revisión nueva.
- Si una migración falla, la app no arranca a medias: informa el error, conserva la copia previa y
  los datos quedan intactos. No reintentar a mano sobre la base del cliente sin esa copia.

---

## Qué pasa en la PC del cliente

Cuando hace doble clic en `EscanAppSetup.exe`:

1. Acepta la licencia y elige si quiere el ícono en el Escritorio.
2. Se copian los archivos a `C:\Program Files\EscanApp`.
3. Se ejecuta `postinstall.ps1`, que en una consola con progreso:
   - busca Ollama; **si ya lo tiene, no lo reinstala**;
   - si no lo tiene, lo instala en silencio;
   - espera a que el servidor de Ollama responda;
   - descarga el modelo base `qwen2.5:0.5b` (~400 MB);
   - crea los **9 modelos** desde los Modelfiles.
4. Se abre EscanApp.

**Primera instalación: 5–15 minutos**, casi todo descarga. Las siguientes son casi instantáneas porque Ollama y los modelos ya están.

### Si el cliente no tiene internet en ese momento

La instalación **no falla**. Avisa, termina bien, y la aplicación **se repara sola** en el primer arranque con conexión: `Backend/agent/provisioning.py` verifica los 9 modelos en cada arranque y crea los que falten, en segundo plano. El cliente nunca abre una consola.

---

## Instalador offline (opcional)

Si necesitás instalar en una PC sin internet, podés incluir Ollama dentro del instalador:

1. Bajá `OllamaSetup.exe` de https://ollama.com/download/windows
2. Dejalo en `installer\vendor\OllamaSetup.exe`
3. Corré `build_release.bat`

El build lo detecta y avisa **`Modo OFFLINE`**. El instalador queda ~1 GB en vez de ~60 MB.

**Ojo:** esto solo resuelve la instalación de *Ollama*. El **modelo base sigue necesitando internet** (`ollama pull`). Para un despliegue 100% offline hay que copiar también la carpeta `%USERPROFILE%\.ollama\models` desde una máquina que ya tenga los modelos creados.

---

## Dónde quedan los datos del cliente

```
%LOCALAPPDATA%\EscanApp\
├── pos.db              ← base de datos (productos, ventas) + versión de esquema
├── backups\            ← copias automáticas y previas a migrar/restaurar (últimas 5)
├── Modelfiles\         ← copia editable de los 9 Modelfiles
└── logs\
    ├── escanapp.log    ← log de la aplicación (incluye la revisión de esquema)
    └── install.log     ← log del aprovisionamiento de IA
```

**Por qué no en `C:\Program Files`:** Windows no deja escribir ahí a un usuario sin permisos de administrador. Si la base de datos viviera junto al `.exe`, la primera venta fallaría con *"attempt to write a readonly database"*. Ese era el bug más grave del empaquetado anterior.

Cuando pidas un log para dar soporte, es `%LOCALAPPDATA%\EscanApp\logs\escanapp.log`.

---

## Diagnóstico

La app expone su estado en `http://127.0.0.1:8000/api/system/status`:

```json
{
  "version": "1.0.0",
  "data_dir": "C:\\Users\\cliente\\AppData\\Local\\EscanApp",
  "schema_revision": "0001",
  "schema_is_head": true,
  "ollama_available": true,
  "base_model": "qwen2.5:0.5b",
  "base_model_ready": true,
  "missing_models": [],
  "models_ready": true,
  "provisioning": false,
  "last_error": null
}
```

- `schema_revision` / `schema_is_head` → en qué migración está la base del cliente.
- `ollama_available: false` → Ollama no está corriendo.
- `missing_models` no vacío → se están creando (o falló la creación; mirá `last_error`).
- `POST /api/system/provision` fuerza un reintento.
