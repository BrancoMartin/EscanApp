## Why

EscanApp hoy solo corre en la máquina de desarrollo. Para venderlo como producto comercial, un usuario final debe poder descargar **un único archivo `EscanAppSetup.exe`**, hacer doble clic, esperar unos minutos y usar la aplicación con los 9 agentes de IA funcionando, **sin instalar Python, Node, Visual C++, sin abrir CMD, sin crear modelos a mano y sin tocar variables de entorno**.

El estado actual no permite eso. El análisis del proyecto encontró seis defectos que romperían la instalación en cualquier PC que no sea la del desarrollador:

1. **`requirements.txt` incompleto**: faltan `langchain`, `langchain-ollama` y `pyinstaller`. Un build limpio en otra máquina falla.
2. **La base de datos se escribe en la carpeta de instalación**: `Backend/database.py` resuelve `dirname(sys.executable)` cuando está congelado, o sea `C:\Program Files\EscanApp\pos.db`. Esa ruta **no es escribible** por un usuario estándar de Windows (UAC / ACL de Program Files): la primera venta reventaría con `sqlite3.OperationalError: attempt to write a readonly database`.
3. **Modelo base incoherente**: `Backend/.env` fija `OLLAMA_MODEL=gemma3:4b` (3.3 GB) mientras los 9 Modelfiles declaran `FROM qwen2.5:0.5b` (~400 MB). El instalador bajaría 3.3 GB de un modelo que la app no usa.
4. **`Modelfiles/GeneralConsultant` tiene BOM UTF-8** antes de `FROM`, lo que puede hacer fallar el parseo de `ollama create`.
5. **`pos.spec` empaqueta la carpeta `Backend` entera**: incluye `openspec/`, `CurrencyMicroservice/` (C#/.NET, que no corre en el .exe), `.claude/` y el `.env` con configuración interna. Basura en el instalador y filtración de configuración.
6. **PyInstaller en modo onefile**: descomprime ~25 MB a `%TEMP%` en **cada** arranque. Para un producto comercial es un arranque lento e innecesario.

Además no existe ningún automatismo de release: hoy hay que correr `npm run build`, `PyInstaller`, `crear_modelos.bat` y copiar archivos a mano.

## What Changes

Se agrega una nueva capability **`packaging`** que cubre el empaquetado, la instalación y el aprovisionamiento automático del entorno de IA en la máquina del usuario final.

- **Instalador único `EscanAppSetup.exe`** construido con **Inno Setup**, con icono, licencia, versión, publisher, accesos directos (escritorio + menú inicio), desinstalador y ejecución de la app al finalizar.
- **Aprovisionamiento automático de Ollama en la post-instalación**: detectar si Ollama ya existe; instalarlo en silencio solo si falta; esperar a que el servidor HTTP quede operativo; hacer `ollama pull` del modelo base; y crear los **9 modelos personalizados** a partir de los Modelfiles.
- **Separación de rutas de runtime**: los datos de usuario (base de datos, logs, Modelfiles) pasan a `%LOCALAPPDATA%\EscanApp`, que **sí** es escribible. La carpeta de instalación queda de solo lectura, como corresponde a un producto Windows.
- **Autorreparación en runtime**: si al arrancar faltan modelos (instalación sin internet, usuario que borró un modelo, Ollama reinstalado), la app los recrea sola en segundo plano en vez de fallar.
- **Un único comando de build**: `scripts\build_release.bat` limpia, compila el frontend, corre PyInstaller, copia recursos y genera el instalador firmado con la versión que dice el archivo `VERSION`.
- **Versionado único**: un archivo `VERSION` en la raíz es la fuente de verdad para el .exe, el instalador y el registro de Windows. Subir de versión = editar `VERSION` y correr `build_release.bat`.
- Se corrigen los seis defectos listados arriba.

## Capabilities

### Added Capabilities
- `packaging`: empaquetado del producto, instalador Windows, aprovisionamiento automático de Ollama y sus 9 modelos, rutas de datos de usuario, versionado y proceso de release.

### Modified Capabilities
- `ai-agent`: el modelo base queda unificado en `qwen2.5:0.5b`, los 9 modelos se aprovisionan automáticamente (no manualmente con `crear_modelos.bat`) y el sistema se autorrepara si faltan.

## Impact

**Archivos nuevos**
- `VERSION` — fuente de verdad de la versión.
- `Backend/runtime.py` — resolución de rutas según entorno (desarrollo vs. instalado).
- `Backend/agent/provisioning.py` — verificación y creación automática de los 9 modelos.
- `installer/EscanApp.iss` — script de Inno Setup.
- `installer/postinstall.ps1` — detección/instalación de Ollama, pull del base, creación de modelos.
- `installer/LICENSE.txt` — licencia mostrada en el instalador.
- `scripts/build_release.bat` + `scripts/build_release.ps1` — build de una sola pasada.
- `docs/RELEASE.md` — cómo publicar una versión nueva.

**Archivos modificados**
- `requirements.txt` — dependencias completas y fijadas.
- `pos.spec` — onedir, `datas` filtrado, versión e icono.
- `Backend/database.py` — la DB vive en `%LOCALAPPDATA%\EscanApp`.
- `Backend/api/app.py` — rutas vía `Backend/runtime.py`; endpoint de estado del sistema.
- `Backend/agent/ollama_client.py` — modelo base `qwen2.5:0.5b`; sin dependencia del `.env` empaquetado.
- `Backend/.env` → `Backend/.env.example` — el `.env` deja de empaquetarse.
- `Modelfiles/GeneralConsultant` — se elimina el BOM.
- `main.py` — arranque tolerante a fallos, logs a archivo, splash mientras aprovisiona.

**No cambia**
- El contrato HTTP de la API, los modelos de datos, la lógica de negocio ni el frontend React. La app en desarrollo (`python main.py`) sigue funcionando exactamente igual.
