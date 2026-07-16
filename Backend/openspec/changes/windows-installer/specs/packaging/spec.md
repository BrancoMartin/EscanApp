## ADDED Requirements

### Requirement: Instalador único de Windows

El sistema SHALL distribuirse como un único archivo ejecutable `EscanAppSetup.exe`, construido con Inno Setup, que instale el producto completo sin que el usuario final necesite instalar Python, Node.js, dependencias, Visual C++, abrir una consola, ejecutar comandos, crear modelos de IA a mano ni modificar variables de entorno.

El instalador SHALL declarar icono personalizado, licencia, versión, nombre de programa y publisher, y SHALL requerir privilegios de administrador.

El instalador SHALL usar un `AppId` (GUID) fijo e inmutable entre versiones, de modo que instalar una versión nueva sobre una existente sea una actualización in-place y no una segunda instalación paralela.

#### Scenario: Instalación en una PC limpia

- **WHEN** un usuario descarga `EscanAppSetup.exe` en una PC Windows sin Python, sin Node y sin Ollama, y hace doble clic
- **THEN** el instalador se ejecuta hasta el final y la aplicación queda utilizable con sus 9 agentes de IA, sin ningún paso manual adicional

#### Scenario: Actualización sobre una versión anterior

- **WHEN** el usuario ejecuta el instalador de la versión 1.1.0 sobre una instalación existente de la 1.0.0
- **THEN** la instalación se actualiza in-place, se conserva la base de datos del usuario y NO aparece una segunda entrada en "Agregar o quitar programas"

### Requirement: Accesos directos y desinstalador

El instalador SHALL crear un acceso directo en el Menú Inicio y, de forma opcional para el usuario, uno en el Escritorio.

El instalador SHALL registrar un desinstalador en "Agregar o quitar programas" de Windows.

El desinstalador SHALL preguntar al usuario si desea eliminar también sus datos (base de datos). Si el usuario no lo confirma, los datos en `%LOCALAPPDATA%\EscanApp` SHALL conservarse.

#### Scenario: Desinstalación conservando datos

- **WHEN** el usuario desinstala EscanApp y responde "No" a la pregunta de eliminar los datos
- **THEN** la carpeta de instalación se elimina pero `%LOCALAPPDATA%\EscanApp\pos.db` permanece intacta, y una reinstalación posterior recupera su base de datos

### Requirement: Aprovisionamiento automático de Ollama

El instalador SHALL detectar si Ollama ya está instalado en la máquina, y SHALL instalarlo únicamente si no existe.

Cuando deba instalarlo, el instalador SHALL usar una copia vendorizada en `installer/vendor/OllamaSetup.exe` si está presente; de lo contrario SHALL descargar el instalador oficial desde internet. La instalación de Ollama SHALL ser silenciosa (sin interacción del usuario).

Tras instalar o detectar Ollama, el sistema SHALL esperar a que el servidor HTTP de Ollama quede operativo en `http://127.0.0.1:11434` antes de continuar, con un tiempo máximo de espera acotado.

#### Scenario: Ollama ya presente

- **WHEN** el instalador corre en una PC que ya tiene Ollama instalado
- **THEN** NO lo reinstala, y continúa directamente al aprovisionamiento de modelos

#### Scenario: Ollama ausente

- **WHEN** el instalador corre en una PC sin Ollama
- **THEN** lo instala en silencio y espera a que su servidor responda antes de crear los modelos

### Requirement: Aprovisionamiento automático de los modelos de IA

El sistema SHALL descargar automáticamente el modelo base `qwen2.5:0.5b` mediante `ollama pull`, y SHALL crear automáticamente los 9 modelos personalizados a partir de los Modelfiles del producto, mediante `ollama create <tag> -f <Modelfile>`.

Los 9 tags SHALL ser: `cualifiquer-intent`, `create-product`, `increase-detector`, `attribute-extractor`, `attribute-classifier`, `attribute-resolver`, `incomplet-handler`, `general-consultant`, `create-categories-by-products`.

El aprovisionamiento SHALL ser idempotente: un modelo que ya existe NO SHALL volver a descargarse ni recrearse.

Los Modelfiles SHALL estar codificados en UTF-8 sin BOM, dado que un BOM antes de la directiva `FROM` puede impedir el parseo por parte de Ollama.

#### Scenario: Creación de los 9 modelos

- **WHEN** finaliza la instalación en una PC con conexión a internet
- **THEN** `ollama list` muestra los 9 modelos personalizados, además del modelo base

#### Scenario: Aprovisionamiento idempotente

- **WHEN** el usuario reinstala el producto sobre una máquina que ya tiene los 9 modelos creados
- **THEN** el aprovisionamiento no vuelve a descargar el modelo base ni recrea los modelos existentes

### Requirement: Autorreparación del entorno de IA en el arranque

La aplicación SHALL verificar en cada arranque, en segundo plano y sin bloquear la interfaz, que el modelo base y los 9 modelos personalizados existan en Ollama, y SHALL crear los que falten.

Cuando el aprovisionamiento haya fallado durante la instalación (por ejemplo, por falta de conexión a internet), la aplicación SHALL repararlo por sí sola en el siguiente arranque con conexión, sin intervención del usuario.

El sistema SHALL exponer el estado del entorno de IA en `GET /api/system/status`, incluyendo si Ollama está disponible, qué modelos faltan y si hay un aprovisionamiento en curso.

#### Scenario: Instalación sin internet, reparación posterior

- **WHEN** el usuario instala el producto sin conexión a internet y luego abre la aplicación con conexión
- **THEN** la aplicación descarga el modelo base y crea los 9 modelos en segundo plano, y queda operativa sin que el usuario ejecute ningún comando

#### Scenario: Modelo borrado manualmente

- **WHEN** un modelo personalizado es eliminado de Ollama y el usuario abre la aplicación
- **THEN** la aplicación detecta el faltante y lo recrea a partir del Modelfile correspondiente

### Requirement: Separación de rutas de recursos y datos de usuario

La aplicación SHALL distinguir entre la raíz de **recursos** (solo lectura, dentro de la carpeta de instalación o del bundle de PyInstaller) y la raíz de **datos de usuario** (escritura).

Cuando la aplicación corre instalada, la raíz de datos de usuario SHALL ser `%LOCALAPPDATA%\EscanApp` y NUNCA la carpeta de instalación, dado que `C:\Program Files` no es escribible por un usuario estándar de Windows.

La base de datos SQLite, los logs y los Modelfiles de trabajo SHALL residir en la raíz de datos de usuario.

En el primer arranque de cada usuario, si no existe una base de datos en su raíz de datos, el sistema SHALL sembrarla copiando la base de datos inicial incluida en el producto.

#### Scenario: Primera venta de un usuario estándar

- **WHEN** un usuario sin privilegios de administrador instala la aplicación y registra una venta
- **THEN** la venta se guarda correctamente en `%LOCALAPPDATA%\EscanApp\pos.db` y NO ocurre ningún error de base de datos de solo lectura

#### Scenario: Siembra de la base inicial

- **WHEN** un usuario abre la aplicación por primera vez y no tiene base de datos propia
- **THEN** el sistema copia la base de datos inicial a su carpeta de datos y la aplicación arranca con el catálogo inicial

### Requirement: Build de release con un único comando

El proyecto SHALL proveer un único comando, `scripts\build_release.bat`, que ejecute el proceso completo de release sin pasos manuales: limpiar artefactos previos, instalar dependencias, compilar el frontend React a `Frontend/dist`, ejecutar PyInstaller, copiar los recursos necesarios y generar el instalador final en `release/`.

El build SHALL fallar de forma explícita y con un mensaje claro si falta una herramienta requerida (Node.js, Python, Inno Setup) o si alguno de los pasos falla, y NUNCA SHALL producir un instalador a partir de un build parcial.

#### Scenario: Build completo

- **WHEN** el desarrollador ejecuta `scripts\build_release.bat` en una máquina con Node, Python e Inno Setup
- **THEN** se genera `release\EscanAppSetup-<version>.exe` sin que el desarrollador ejecute ningún otro comando

#### Scenario: Falta una herramienta

- **WHEN** el desarrollador ejecuta el build en una máquina sin Inno Setup instalado
- **THEN** el build se detiene con un mensaje que indica exactamente qué falta y cómo instalarlo, y no genera ningún artefacto

### Requirement: Versionado único del producto

El archivo `VERSION` en la raíz del proyecto SHALL ser la única fuente de verdad de la versión del producto, en formato semántico `MAJOR.MINOR.PATCH`.

El proceso de build SHALL propagar esa versión al recurso de versión del ejecutable de Windows, a los metadatos del instalador y al nombre del artefacto de release.

Publicar una versión nueva SHALL requerir únicamente editar `VERSION` y ejecutar `scripts\build_release.bat`.

#### Scenario: Publicación de una versión nueva

- **WHEN** el desarrollador cambia el contenido de `VERSION` a `1.1.0` y ejecuta `scripts\build_release.bat`
- **THEN** se genera `release\EscanAppSetup-1.1.0.exe`, y tanto las Propiedades del ejecutable como "Agregar o quitar programas" muestran la versión 1.1.0
