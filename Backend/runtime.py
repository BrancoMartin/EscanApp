"""Resolucion de rutas segun el entorno de ejecucion.

El producto vive en dos entornos distintos y las rutas NO son las mismas:

  - Desarrollo: todo cuelga de la raiz del repo.
  - Instalado:  el ejecutable vive en C:\\Program Files\\EscanApp, que Windows
                deja de SOLO LECTURA para un usuario sin elevacion. Escribir la
                base de datos ahi falla con "attempt to write a readonly
                database" apenas el usuario registra una venta.

Por eso se separan tres raices:

  resource_dir()  recursos de solo lectura (bundle de PyInstaller o repo)
  data_dir()      datos del usuario, escribibles (%LOCALAPPDATA%\\EscanApp)
  log_dir()       logs de la aplicacion

En desarrollo las tres apuntan a la raiz del repo, para no cambiar el flujo de
trabajo actual.
"""

import os
import shutil
import sys

APP_NAME = "EscanApp"

# Directorio de este archivo: Backend/
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# Raiz del repo en desarrollo: un nivel arriba de Backend/
_REPO_ROOT = os.path.abspath(os.path.join(_BACKEND_DIR, ".."))


def is_frozen():
    """True cuando corre dentro del ejecutable de PyInstaller."""
    return getattr(sys, "frozen", False) is True


def resource_dir():
    """Raiz de los recursos de solo lectura (Frontend/dist, Modelfiles, migraciones)."""
    if is_frozen():
        # PyInstaller 6 en onedir define sys._MEIPASS apuntando a _internal/,
        # que es donde quedan los datas. El fallback cubre builds viejos.
        bundle = getattr(sys, "_MEIPASS", None)
        if bundle:
            return bundle
        return os.path.dirname(os.path.abspath(sys.executable))
    return _REPO_ROOT


def data_dir():
    """Raiz escribible con los datos del usuario. Se crea si no existe.

    ESCANAPP_DATA_DIR permite apuntarla a otro lado: sirve para probar contra una
    base descartable sin tocar la real, y para mover los datos a otra unidad.
    """
    override = os.environ.get("ESCANAPP_DATA_DIR")
    if override:
        path = override
    elif is_frozen():
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            base = os.path.expanduser("~")
        path = os.path.join(base, APP_NAME)
    else:
        path = _REPO_ROOT
    os.makedirs(path, exist_ok=True)
    return path


def log_dir():
    """Carpeta de logs. En desarrollo, la raiz del repo."""
    if is_frozen():
        path = os.path.join(data_dir(), "logs")
    else:
        path = _REPO_ROOT
    os.makedirs(path, exist_ok=True)
    return path


def db_path():
    """Ruta absoluta de la base de datos SQLite del usuario."""
    return os.path.join(data_dir(), "pos.db")


def seed_db_path():
    """Ruta de la base de datos inicial incluida en el producto (puede no existir).

    Empaquetada vive en la raiz del bundle (pos.spec la copia ahi). En desarrollo
    se busca en ``installer/seed/pos.db`` y NO en la raiz del repo: ahi esta el
    ``pos.db`` de trabajo, con datos reales. Sin esta separacion, cualquier prueba
    con ``ESCANAPP_DATA_DIR`` copiaria la base de desarrollo dentro de la carpeta
    descartable.
    """
    if is_frozen():
        return os.path.join(resource_dir(), "pos.db")
    return os.path.join(_REPO_ROOT, "installer", "seed", "pos.db")


def migrations_dir():
    """Carpeta con el entorno y las revisiones de Alembic.

    Son recursos de SOLO LECTURA: viajan dentro del bundle (pos.spec los copia
    a Backend/migrations) y en desarrollo viven en el repo.
    """
    return os.path.join(resource_dir(), "Backend", "migrations")


def backups_dir():
    """Carpeta escribible con las copias de seguridad de la base del usuario."""
    path = os.path.join(data_dir(), "backups")
    os.makedirs(path, exist_ok=True)
    return path


def modelfiles_dir():
    """Carpeta de Modelfiles de trabajo, dentro de los datos del usuario."""
    path = os.path.join(data_dir(), "Modelfiles")
    os.makedirs(path, exist_ok=True)
    return path


def seed_modelfiles_dir():
    """Carpeta de Modelfiles incluida en el producto (solo lectura)."""
    return os.path.join(resource_dir(), "Modelfiles")


def version():
    """Version del producto, leida del archivo VERSION. '0.0.0' si no esta."""
    path = os.path.join(resource_dir(), "VERSION")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except OSError:
        return "0.0.0"


def ensure_user_data():
    """Prepara la carpeta de datos del usuario en el primer arranque.

    Idempotente: si los archivos ya existen no los pisa, para no destruir los
    datos ni las personalizaciones del usuario.
    """
    ensure_seed_database()
    ensure_modelfiles()


def ensure_seed_database():
    """Siembra la base inicial la primera vez que un usuario abre la app.

    La siembra ocurre por-usuario y en el arranque (no en el instalador) porque
    el instalador corre elevado y una sola vez por maquina: no sabria a que
    perfiles copiarle la base en una PC compartida.

    Sin semilla (el caso normal desde que el esquema lo crean las migraciones),
    devuelve False y Alembic crea las tablas vacias en el primer arranque. Se
    conserva para el dia que se envien datos precargados (un catalogo inicial).
    """
    target = db_path()
    if os.path.exists(target):
        return False

    seed = seed_db_path()
    if not os.path.exists(seed):
        # Sin semilla: las tablas vacias las crea la migracion base de Alembic.
        return False

    # No sembrar sobre si mismo en desarrollo (seed y target son el mismo path).
    if os.path.abspath(seed) == os.path.abspath(target):
        return False

    shutil.copy2(seed, target)
    return True


def ensure_modelfiles():
    """Copia los Modelfiles del producto a la carpeta de datos del usuario.

    Los deja donde el aprovisionamiento los va a buscar y donde un usuario
    avanzado puede editarlos. No pisa un Modelfile ya existente.
    """
    seed = seed_modelfiles_dir()
    if not os.path.isdir(seed):
        return 0

    target = modelfiles_dir()
    if os.path.abspath(seed) == os.path.abspath(target):
        return 0

    copied = 0
    for name in os.listdir(seed):
        source = os.path.join(seed, name)
        if not os.path.isfile(source):
            continue
        destination = os.path.join(target, name)
        if os.path.exists(destination):
            continue
        shutil.copy2(source, destination)
        copied += 1
    return copied
