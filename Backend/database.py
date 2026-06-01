import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os


class Base(DeclarativeBase):
    pass


def get_db_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

BASE_DIR = get_db_path()
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'pos.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # crea las tablas en la base de datos si no existen
    from Backend.models import product, sale, item_sale
    from Backend.models.category import Category
    from Backend.models.value import Value
    from Backend.models.product_value import ProductValue
    Base.metadata.create_all(bind=engine)

def get_db():
    # Generador de sesión para usar como dependencia en FastAPI
    db = SessionLocal()
    try:
        yield db
    finally:
        # Cerramos la sesión siempre, haya error o no
        db.close()
