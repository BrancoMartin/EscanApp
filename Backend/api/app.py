from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # para servir archivos estáticos (css, js)
from fastapi.responses import FileResponse   # para devolver archivos como respuesta
from database import init_db     # función que crea las tablas
from api.routes import controller_products, controller_sales
import os  # para manejar rutas de archivos y carpetas

def create_app() -> FastAPI:  # -> FastAPI indica que esta función devuelve una app FastAPI
    app = FastAPI()            # creamos la instancia de FastAPI

    # Permite que el frontend en Vite acceda a esta API durante desarrollo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inicializamos la base de datos al arrancar
    init_db()

    app.include_router(controller_products.router, prefix="/api/products")
    app.include_router(controller_sales.router, prefix="/api/sales")
    

    # Endpoint de salud que usa main.py para saber si el servidor está listo
    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Construimos la ruta absoluta a la carpeta dist de React
    # __file__ es la ruta de este archivo (app.py)
    # .. sube un nivel, ../.. sube dos niveles hasta llegar a la raíz
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
    
    if os.path.exists(frontend_dist):  # solo si el build de React existe
        # Servimos los archivos estáticos (js, css, imágenes) desde /assets
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

        # Cualquier ruta que no sea /api devuelve el index.html de React
        
        @app.get("/{full_path:path}")
        def serve_frontend(full_path: str):
            if full_path.startswith("api"):
                from fastapi import Response
                return Response(status_code=404)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

    return app
