import os  # para manejar rutas de archivos y carpetas
import threading  # para precargar el modelo de IA sin bloquear el arranque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # para servir archivos estáticos (css, js)
from fastapi.responses import FileResponse   # para devolver archivos como respuesta
from Backend import runtime                  # rutas segun el entorno (desarrollo / instalado)
from Backend.database import init_db     # función que crea las tablas
from Backend.api.routes import controller_products, controller_sales, controller_agent, controller_attributes_new
from Backend.agent import provisioning   # verificación y reparación del entorno de IA
from Backend.agent.ollama_client import warmup  # precarga del modelo de intent

def create_app() -> FastAPI:  # -> FastAPI indica que esta función devuelve una app FastAPI
    app = FastAPI(title="EscanApp", version=runtime.version())  # creamos la instancia de FastAPI

    # Permite que el frontend en Vite acceda a esta API durante desarrollo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inicializamos la base de datos al arrancar
    init_db()

    # Verificamos el entorno de IA en segundo plano y creamos los modelos que
    # falten. Cubre la instalación sin internet y el modelo borrado a mano: la
    # app se repara sola en vez de tirar errores crípticos.
    provisioning.ensure_models_async()

    # Precargamos el modelo de intent en segundo plano: asi el primer mensaje
    # del usuario no paga la carga del modelo. Daemon para no bloquear el
    # arranque ni impedir el cierre del proceso.
    threading.Thread(target=warmup, daemon=True).start()

    app.include_router(controller_products.router, prefix="/api/products")
    app.include_router(controller_sales.router, prefix="/api/sales")
    app.include_router(controller_agent.router, prefix="/api/agent")
    app.include_router(controller_attributes_new.router, prefix="/api")


    # Endpoint de salud que usa main.py para saber si el servidor está listo
    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Estado del entorno de IA. El frontend lo usa para avisar "preparando los
    # agentes..." mientras se descargan o crean los modelos.
    @app.get("/api/system/status")
    def system_status():
        state = provisioning.status()
        return {
            "version": runtime.version(),
            "data_dir": runtime.data_dir(),
            "ollama_available": state["ollama_available"],
            "base_model": provisioning.BASE_MODEL,
            "base_model_ready": state["base_model_ready"],
            "missing_models": state["missing_models"],
            "models_ready": len(state["missing_models"]) == 0,
            "provisioning": state["provisioning"],
            "last_error": state["last_error"],
        }

    # Reparación manual del entorno de IA (botón "reintentar" del frontend).
    @app.post("/api/system/provision")
    def system_provision():
        state = provisioning.status()
        if state["provisioning"]:
            return {"started": False, "reason": "Ya hay un aprovisionamiento en curso."}
        provisioning.ensure_models_async()
        return {"started": True}

    # El frontend compilado es un recurso de SOLO LECTURA: vive dentro del
    # bundle cuando la app está instalada y en el repo durante el desarrollo.
    # runtime.resource_dir() resuelve las dos situaciones.
    frontend_dist = os.path.join(runtime.resource_dir(), "Frontend", "dist")

    if os.path.exists(frontend_dist):  # solo si el build de React existe
        # Servimos los archivos estáticos (js, css, imágenes) desde /assets
        assets_dir = os.path.join(frontend_dist, "assets")
        if os.path.isdir(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        app.mount(
            "/static",
            StaticFiles(directory=frontend_dist),
            name="static",
        )

        # Cualquier ruta que no sea /api devuelve el index.html de React
        @app.get("/{full_path:path}")
        def serve_frontend(full_path: str):
            if full_path.startswith("api"):
                from fastapi import Response
                return Response(status_code=404)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

    return app
