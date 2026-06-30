import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # para servir archivos estáticos (css, js)
from fastapi.responses import FileResponse   # para devolver archivos como respuesta
from Backend.database import init_db     # función que crea las tablas
from Backend.api.routes import controller_products, controller_sales, controller_agent, controller_attributes_new, controller_stock
import os  # para manejar rutas de archivos y carpetas

def create_app() -> FastAPI:  # -> FastAPI indica que esta función devuelve una app FastAPI
    app = FastAPI()            # creamos la instancia de FastAPI

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

    app.include_router(controller_products.router, prefix="/api/products")
    app.include_router(controller_sales.router, prefix="/api/sales")
    app.include_router(controller_agent.router, prefix="/api/agent")
    app.include_router(controller_attributes_new.router, prefix="/api")
    app.include_router(controller_stock.router, prefix="/api/stock")
    

    # Endpoint de salud que usa main.py para saber si el servidor está listo
    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    def get_base_path():
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS  # ruta temporal cuando corre como .exe
        return os.path.join(os.path.dirname(__file__), '..', '..')

   
    frontend_dist = os.path.join(get_base_path(), "Frontend", "dist")
    print("Buscando frontend en:", os.path.abspath(frontend_dist))
    print("Existe:", os.path.exists(frontend_dist))
    
    if os.path.exists(frontend_dist):  # solo si el build de React existe
        # Servimos los archivos estáticos (js, css, imágenes) desde /assets
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

        # Cualquier ruta que no sea /api devuelve el index.html de React
        print("Montando ruta para frontend")
        @app.get("/{full_path:path}")
        def serve_frontend(full_path: str):
            if full_path.startswith("api"):
                from fastapi import Response
                return Response(status_code=404)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

    return app
