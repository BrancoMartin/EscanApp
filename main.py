"""Punto de entrada de EscanApp.

En desarrollo:  python main.py            (abre la ventana)
                python main.py --no-window  (solo el servidor, para probar la API)

Instalado:      EscanApp.exe
"""

import os
import socket
import sys
import threading
import time
import traceback
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Backend'))

from Backend import runtime

HOST = "127.0.0.1"
DEFAULT_PORT = 8000

# El puerto real se resuelve al arrancar: si el 8000 esta ocupado (otra copia de
# la app, otro programa), buscamos uno libre en vez de morir. El frontend en
# produccion usa URLs relativas, asi que no le importa en que puerto quedamos.
PORT = DEFAULT_PORT


def setup_logging():
    """Con console=False, PyInstaller deja sys.stdout en None y cualquier print()
    revienta con AttributeError. Redirigimos la salida a un archivo de log."""
    if not runtime.is_frozen():
        return None

    path = os.path.join(runtime.log_dir(), "escanapp.log")
    handle = open(path, "a", encoding="utf-8", buffering=1)
    sys.stdout = handle
    sys.stderr = handle
    print("\n" + "=" * 60)
    print(f"EscanApp {runtime.version()} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Datos del usuario: {runtime.data_dir()}")
    print("=" * 60)
    return path


def find_free_port(preferred):
    """Devuelve el puerto preferido si esta libre; si no, uno que el SO elija."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((HOST, preferred))
            return preferred
        except OSError:
            pass

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((HOST, 0))
        return probe.getsockname()[1]


def start_server():
    import uvicorn
    from Backend.api.app import create_app

    app = create_app()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


def wait_server(timeout=60):
    """Espera a que el backend responda /health. False si no arranco a tiempo."""
    deadline = time.time() + timeout
    url = f"http://{HOST}:{PORT}/health"
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def fatal(message):
    """Un error que impide arrancar tiene que ser visible: sin consola, un print
    no lo ve nadie. Lo dejamos en el log y lo mostramos en un cuadro de dialogo."""
    print(f"[FATAL] {message}")
    traceback.print_exc()
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                None,
                f"{message}\n\nDetalle en:\n{os.path.join(runtime.log_dir(), 'escanapp.log')}",
                "EscanApp",
                0x10,  # MB_ICONERROR
            )
        except Exception:
            pass


def main():
    global PORT

    setup_logging()
    PORT = find_free_port(DEFAULT_PORT)
    print(f"[MAIN] Servidor en http://{HOST}:{PORT}")

    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()

    if not wait_server():
        fatal("El servidor interno no arrancó. La aplicación no puede continuar.")
        return 1

    if "--no-window" in sys.argv:
        # Mantiene el servidor corriendo hasta que apretés Ctrl+C
        print("Servidor corriendo en modo desarrollo. Presioná Ctrl+C para detener.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Servidor detenido.")
        return 0

    import webview

    webview.create_window(
        title="EscanApp",
        url=f"http://{HOST}:{PORT}",
        width=1100,
        height=700,
        resizable=True,
    )
    webview.start()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        fatal(f"Error inesperado al iniciar EscanApp: {error}")
        sys.exit(1)
