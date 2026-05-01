import sys

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import threading
import time
import webview
import uvicorn
from backend.api.app import create_app

HOST = "127.0.0.1"
PORT = 8000


sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def start_server():
    app = create_app()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

def wait_server():
    import urllib.request
    while True:
        try:
            urllib.request.urlopen(f"http://{HOST}:{PORT}/health")
            break
        except:
            time.sleep(0.2)
if __name__ == "__main__":
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()
    wait_server()

    if "--no-window" not in sys.argv:
        webview.create_window(
            title="POS",
            url=f"http://{HOST}:{PORT}",
            width=1100,
            height=700,
            resizable=True,
        )
        webview.start()
    else:
        # Mantiene el servidor corriendo hasta que apretés Ctrl+C
        print("Servidor corriendo en modo desarrollo. Presioná Ctrl+C para detener.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Servidor detenido.")