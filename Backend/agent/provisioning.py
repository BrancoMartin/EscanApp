"""Aprovisionamiento y autorreparacion del entorno de IA (Ollama + 9 modelos).

El instalador hace el trabajo pesado (instalar Ollama, pull del modelo base,
create de los 9 modelos). Pero ese paso puede fallar por razones que no
controlamos: la PC no tenia internet en ese momento, un antivirus lo bloqueo,
el usuario cancelo, o mas adelante alguien borro un modelo o reinstalo Ollama.

Por eso la app REPITE la verificacion en cada arranque, en segundo plano. Es
barata cuando todo esta bien (una sola llamada HTTP local) y convierte una
instalacion a medias en algo que se repara solo, sin que el usuario tenga que
abrir una consola.
"""

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

from Backend import runtime

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# Modelo base del que derivan los 9 modelos especializados (directiva FROM de
# cada Modelfile). Tiene que ser el mismo en los Modelfiles y aca: si no, el
# aprovisionamiento descarga un modelo que la app no usa.
BASE_MODEL = "qwen2.5:0.5b"

# tag de Ollama -> nombre del Modelfile.
# Es la misma lista que crear_modelos.bat, pero ejecutada automaticamente.
MODELS = {
    "cualifiquer-intent": "CualifiquerIntent",
    "create-product": "CreateProduct",
    "increase-detector": "IncreaseDetector",
    "attribute-extractor": "AttributeExtractor",
    "attribute-classifier": "AttributeClassifier",
    "attribute-resolver": "AttributeResolver",
    "incomplet-handler": "IncompletHandler",
    "general-consultant": "GeneralConsultant",
    "create-categories-by-products": "CreateCategories",
}

# Timeouts generosos: descargar el modelo base en una conexion lenta puede
# tardar varios minutos y no queremos abortar a mitad de camino.
PULL_TIMEOUT = 1800   # 30 min
CREATE_TIMEOUT = 300  # 5 min por modelo

_state = {
    "ollama_available": False,
    "base_model_ready": False,
    "missing_models": list(MODELS.keys()),
    "provisioning": False,
    "last_error": None,
    "last_check": None,
}
_lock = threading.Lock()


def _no_window():
    """Evita que los subprocesos de Ollama abran una consola negra en Windows."""
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW
    return 0


def _run(args, timeout):
    """Ejecuta un comando de Ollama. Devuelve (ok, salida)."""
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=_no_window(),
        )
    except FileNotFoundError:
        return False, "No se encontro el ejecutable de Ollama."
    except subprocess.TimeoutExpired:
        return False, f"Tiempo agotado ejecutando: {' '.join(args)}"

    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode == 0, output.strip()


def ollama_binary():
    """Ruta al ejecutable de Ollama, o None si no esta instalado.

    Se busca en el PATH y en las rutas donde el instalador oficial lo deja.
    El PATH del proceso puede no incluir Ollama si la app arranco antes de que
    el instalador refrescara las variables de entorno de la sesion.
    """
    found = shutil.which("ollama")
    if found:
        return found

    candidates = []
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        candidates.append(os.path.join(local_app, "Programs", "Ollama", "ollama.exe"))
    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidates.append(os.path.join(program_files, "Ollama", "ollama.exe"))

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def installed_models():
    """Modelos presentes en Ollama. None si el servidor no responde.

    Ollama devuelve los tags como 'nombre:latest'; se normaliza para poder
    compararlos con nuestros tags pelados.
    """
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None

    names = set()
    for model in payload.get("models", []):
        name = model.get("name") or model.get("model") or ""
        if not name:
            continue
        names.add(name)
        if name.endswith(":latest"):
            names.add(name[: -len(":latest")])
    return names


def wait_for_server(timeout=60):
    """Espera a que el servidor de Ollama responda. True si quedo operativo."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if installed_models() is not None:
            return True
        time.sleep(1)
    return False


def start_server():
    """Levanta `ollama serve` si el servicio no esta corriendo.

    El instalador oficial de Ollama deja el servicio andando, pero si el
    usuario lo cerro desde la bandeja hay que revivirlo.
    """
    binary = ollama_binary()
    if not binary:
        return False

    try:
        subprocess.Popen(
            [binary, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window(),
        )
    except OSError:
        return False

    return wait_for_server(timeout=30)


def _modelfile_path(modelfile_name):
    """Ruta del Modelfile, priorizando la copia del usuario sobre la del bundle."""
    user_copy = os.path.join(runtime.modelfiles_dir(), modelfile_name)
    if os.path.isfile(user_copy):
        return user_copy

    bundled = os.path.join(runtime.seed_modelfiles_dir(), modelfile_name)
    if os.path.isfile(bundled):
        return bundled
    return None


def missing_models(present=None):
    """Tags de los 9 modelos que faltan crear."""
    if present is None:
        present = installed_models()
    if present is None:
        return list(MODELS.keys())

    missing = []
    for tag in MODELS:
        if tag not in present:
            missing.append(tag)
    return missing


def status():
    """Estado del entorno de IA, para GET /api/system/status."""
    with _lock:
        return dict(_state)


def _set(**updates):
    with _lock:
        _state.update(updates)


def _provision(auto_start):
    """Cuerpo del aprovisionamiento. Ver ensure_models()."""
    # 1. Ollama responde?
    present = installed_models()
    if present is None and auto_start:
        start_server()
        present = installed_models()

    if present is None:
        _set(
            ollama_available=False,
            base_model_ready=False,
            missing_models=list(MODELS.keys()),
            last_error="Ollama no esta disponible en " + OLLAMA_BASE_URL,
            last_check=time.time(),
        )
        return

    _set(ollama_available=True)

    binary = ollama_binary()
    if not binary:
        _set(
            base_model_ready=BASE_MODEL in present,
            missing_models=missing_models(present),
            last_error="No se encontro el ejecutable de Ollama para crear los modelos.",
            last_check=time.time(),
        )
        return

    # 2. Modelo base
    if BASE_MODEL not in present:
        print(f"[PROVISION] Descargando modelo base {BASE_MODEL}...")
        ok, output = _run([binary, "pull", BASE_MODEL], PULL_TIMEOUT)
        if not ok:
            _set(
                base_model_ready=False,
                missing_models=missing_models(present),
                last_error=f"No se pudo descargar {BASE_MODEL}: {output}",
                last_check=time.time(),
            )
            return
        present = installed_models() or present

    _set(base_model_ready=True)

    # 3. Los 9 modelos especializados: solo los que faltan
    for tag in missing_models(present):
        modelfile = _modelfile_path(MODELS[tag])
        if not modelfile:
            _set(last_error=f"No se encontro el Modelfile de '{tag}'.")
            continue

        print(f"[PROVISION] Creando modelo '{tag}'...")
        ok, output = _run([binary, "create", tag, "-f", modelfile], CREATE_TIMEOUT)
        if not ok:
            _set(last_error=f"No se pudo crear '{tag}': {output}")

    final = missing_models()
    _set(missing_models=final, last_check=time.time())
    if not final:
        print("[PROVISION] Entorno de IA listo: los 9 modelos estan disponibles.")


def ensure_models(auto_start=True):
    """Verifica y repara el entorno de IA. Idempotente.

    1. Ollama responde? (si no, se intenta levantar el servidor)
    2. Esta el modelo base? Si no -> ollama pull
    3. Cuales de los 9 faltan? -> ollama create solo de esos

    Devuelve el estado final. No lanza excepciones: si algo falla, lo deja en
    last_error y la app sigue viva (degradada, pero sin reventar).
    """
    _set(provisioning=True, last_error=None)
    try:
        _provision(auto_start)
    finally:
        # El flag se baja ANTES de leer el estado: si no, el snapshot que
        # devolvemos diria provisioning=True cuando ya termino.
        _set(provisioning=False)
    return status()


def ensure_models_async():
    """Corre la verificacion en un hilo daemon, sin bloquear el arranque."""
    thread = threading.Thread(target=ensure_models, name="provisioning", daemon=True)
    thread.start()
    return thread
