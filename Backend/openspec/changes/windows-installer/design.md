# Diseño técnico — Instalador Windows y aprovisionamiento automático

## Contexto

El producto son tres piezas que hoy se ensamblan a mano:

1. **Frontend React/Vite** → se compila a `Frontend/dist` y lo sirve FastAPI como estáticos.
2. **Backend Python** (FastAPI + SQLAlchemy + SQLite + PyWebView) → se congela con PyInstaller en `EscanApp.exe`.
3. **Runtime de IA** (Ollama + 9 modelos derivados de `qwen2.5:0.5b`) → hoy se crea corriendo `crear_modelos.bat` a mano.

La pieza 3 es la que hace difícil el empaquetado: **Ollama no se puede embeber dentro del .exe**. Es un servicio aparte, con su propio instalador, su propio directorio de modelos (`%USERPROFILE%\.ollama`) y su propio servidor HTTP en `127.0.0.1:11434`. Cualquier diseño tiene que tratarlo como una **dependencia externa gestionada**, no como una librería.

## Decisión 1 — Ollama se descarga en la instalación, no se empaqueta

**Opciones**

| Opción | Tamaño de `EscanAppSetup.exe` | Requiere internet | 
|---|---|---|
| (A) Vendorizar `OllamaSetup.exe` dentro del instalador | ~1 GB | No, para Ollama. **Sí igual, para los modelos.** |
| (B) Descargar Ollama durante la post-instalación | ~60 MB | Sí |

**Elegida: (B), con soporte opcional para (A).**

Justificación: el modelo base `qwen2.5:0.5b` **hay que bajarlo de internet sí o sí** (`ollama pull`). Un instalador de 1 GB que igual necesita conexión no compra nada — solo hace la descarga inicial 15× más pesada. Se descarga Ollama en el momento.

Como red de seguridad, el script de post-instalación **usa una copia vendorizada si existe** en `installer/vendor/OllamaSetup.exe`. Eso permite construir una variante offline/enterprise sin cambiar una línea de código: se deja el archivo ahí y `build_release.bat` lo empaqueta. Es un flag, no una bifurcación de arquitectura.

## Decisión 2 — Los datos de usuario salen de `Program Files`

Hoy `Backend/database.py` hace:

```python
if getattr(sys, 'frozen', False):
    return os.path.dirname(sys.executable)   # C:\Program Files\EscanApp
```

Windows **deniega escritura** en `Program Files` a procesos sin elevación (UAC / ACL heredada). SQLite abriría la base en modo lectura y la primera venta fallaría con `attempt to write a readonly database`. Es el bug más grave del empaquetado actual y no se manifiesta en desarrollo porque ahí el .exe corre desde `dist/`.

**Diseño:** se separan explícitamente tres raíces, resueltas en `Backend/runtime.py`:

| Raíz | Desarrollo | Instalado | Contenido |
|---|---|---|---|
| `resource_dir()` | raíz del repo | `sys._MEIPASS` / carpeta del .exe | Frontend/dist, Modelfiles semilla, pos.db semilla — **solo lectura** |
| `data_dir()` | raíz del repo | `%LOCALAPPDATA%\EscanApp` | `pos.db` real, Modelfiles del usuario — **escritura** |
| `log_dir()` | raíz del repo | `%LOCALAPPDATA%\EscanApp\logs` | `escanapp.log` |

En el primer arranque, si `data_dir()/pos.db` no existe, se **siembra** copiando la `pos.db` semilla del bundle. Esto satisface el requisito «copiar automáticamente la base de datos inicial» **sin** que el instalador tenga que adivinar el perfil del usuario: la siembra ocurre por-usuario, la primera vez que cada uno abre la app. Un instalador por-máquina que copiara la DB a un perfil concreto sería incorrecto en una PC con varios usuarios.

Instalar `%LOCALAPPDATA%` también significa que **el desinstalador no borra los datos del negocio** por defecto: se le pregunta al usuario si quiere eliminar la base de datos.

## Decisión 3 — PyInstaller pasa de onefile a onedir

`pos.spec` hoy produce un onefile: en **cada** arranque descomprime ~25 MB a `%TEMP%\_MEIxxxx`, lo que agrega segundos de espera y deja basura si el proceso se mata.

Con onedir (`COLLECT`), el .exe arranca directo desde su carpeta. La compresión la hace el instalador (Inno usa LZMA2), así que el `EscanAppSetup.exe` pesa prácticamente lo mismo. Para software que se instala —en vez de correrse portable— onedir es el modo correcto y es lo que hacen los productos comerciales.

También se filtran los `datas`: hoy se empaqueta `('Backend', 'Backend')` entero, arrastrando `openspec/` (specs internas), `CurrencyMicroservice/` (proyecto C#/.NET que ni siquiera corre dentro del .exe), `.claude/` y el `.env`. Se pasa a incluir **solo** los paquetes Python que el runtime importa, más `Frontend/dist`, `Modelfiles/` y la `pos.db` semilla.

## Decisión 4 — El aprovisionamiento se verifica dos veces: en la instalación y en el arranque

El instalador hace el trabajo pesado (instalar Ollama, `pull`, `create` × 9) porque ahí el usuario ya está esperando y hay una barra de progreso. Pero ese paso puede fallar por razones que no controlamos: sin internet en ese momento, antivirus, el usuario canceló, o más adelante alguien borró un modelo o reinstaló Ollama.

Por eso `Backend/agent/provisioning.py` **repite la verificación en cada arranque**, en un hilo daemon:

1. `GET /api/tags` a Ollama → lista de modelos presentes.
2. Faltantes = los 9 tags esperados − los presentes.
3. Si falta el base → `ollama pull qwen2.5:0.5b`.
4. Por cada tag faltante → `ollama create <tag> -f <Modelfile>`.

Es **idempotente y barato** cuando todo está bien (una llamada HTTP local), y convierte una instalación a medias en algo que se autorrepara solo. La app expone `GET /api/system/status` para que el frontend pueda mostrar «preparando los agentes de IA…» en vez de dar errores crípticos.

Este es el requisito de robustez que diferencia un producto de un script.

## Decisión 5 — Versión única en un archivo `VERSION`

Hoy la versión no existe en ningún lado. Se crea `VERSION` (contenido: `1.0.0`) como fuente de verdad, y `build_release.ps1` la propaga a:

- el recurso de versión del `EscanApp.exe` (lo que muestra Windows en Propiedades),
- `AppVersion` de Inno Setup (lo que muestra Agregar/Quitar programas),
- el nombre del artefacto en `release/`,
- el `AppId` **no** cambia nunca (GUID fijo), para que instalar 1.1.0 sobre 1.0.0 sea una **actualización** y no una segunda copia.

Subir de versión = editar `VERSION` + `build_release.bat`. Nada más.

## Decisión 6 — La estructura del repo se extiende, no se reorganiza

El pedido incluía reorganizar el proyecto. **Recomiendo no mover `Backend/`, `Frontend/`, `Modelfiles/` ni `main.py`.** Moverlos rompería los imports (`from Backend.api.app import create_app`), el `pos.spec`, los paths de OpenSpec (`Backend/openspec/`) y el historial de git, a cambio de cero beneficio funcional. La estructura actual ya es la convencional para este stack.

Lo que sí falta son las capas de **build y distribución**, que se agregan:

```
BarcodePaymentSystem/
├── Backend/          # sin cambios de ubicación
├── Frontend/         # sin cambios de ubicación
├── Modelfiles/       # sin cambios de ubicación
├── main.py           # sin cambios de ubicación
├── pos.spec          # reescrito (onedir + datas filtrado)
├── VERSION           # NUEVO — fuente de verdad de la versión
├── scripts/          # NUEVO — build_release.bat / .ps1
├── installer/        # NUEVO — EscanApp.iss, postinstall.ps1, LICENSE.txt, vendor/
├── release/          # NUEVO — salida: EscanAppSetup-1.0.0.exe
└── docs/             # NUEVO — RELEASE.md
```

Se agregan además `Backend/runtime.py` y `Backend/agent/provisioning.py`, que son código de runtime y por eso viven con el resto del backend.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| La post-instalación necesita internet y puede no haberlo | El instalador no falla: avisa y sigue. La app se autorrepara en el próximo arranque con conexión (Decisión 4). |
| `ollama pull` tarda varios minutos y parece colgado | La post-instalación corre en una consola visible con progreso y mensajes en español. |
| ExecutionPolicy de PowerShell bloquea el script | Se invoca con `-NoProfile -ExecutionPolicy Bypass -File`, que no requiere cambiar la política del sistema. |
| Instalar Ollama requiere elevación | El instalador ya corre elevado (`PrivilegesRequired=admin`, necesario para escribir en Program Files). |
| Antivirus marca el .exe de PyInstaller | Se agrega recurso de versión y metadatos de publisher, que es lo que más reduce falsos positivos. Firma de código: fuera de alcance de este cambio (requiere certificado comprado). |

## Fuera de alcance

- Firma digital con certificado EV (requiere comprar el certificado).
- Auto-update en background (el usuario descarga el nuevo Setup y lo ejecuta encima; el `AppId` fijo lo hace una actualización limpia).
- Instalación de Ollama con soporte GPU específico (se usa el instalador oficial, que ya detecta el hardware).
