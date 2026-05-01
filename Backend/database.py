from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os


# from models import attribute

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, '..', 'pos.db')}"

# Motor de la base de datos
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necesario para SQLite con FastAPI
)

# Clase base de la que van a heredar todos los modelos
Base = declarative_base()

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # crea las tablas en la base de datos si no existen
    from models import product, sale, sale_item
    Base.metadata.create_all(bind=engine)

def get_db():
    # Generador de sesión para usar como dependencia en FastAPI
    db = SessionLocal()
    try:
        yield db
    finally:
        # Cerramos la sesión siempre, haya error o no
        db.close()
