from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from Backend import runtime


class Base(DeclarativeBase):
    pass


# Prepara la carpeta de datos del usuario ANTES de tocar la base: si es su
# primer arranque, siembra pos.db y los Modelfiles. Es idempotente.
runtime.ensure_user_data()

# La base vive en la carpeta de datos del usuario, NO junto al ejecutable.
# Instalada en C:\Program Files, Windows no deja escribir ahi sin elevacion y
# SQLite abriria la base en modo lectura: la primera venta fallaria con
# "attempt to write a readonly database".
BASE_DIR = runtime.data_dir()
DATABASE_URL = f"sqlite:///{runtime.db_path()}"

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
    from Backend.models.attribute import Attribute
    from Backend.models.product_attribute import ProductAttribute
    Base.metadata.create_all(bind=engine)

def get_db():
    # Generador de sesión para usar como dependencia en FastAPI
    db = SessionLocal()
    try:
        yield db
    finally:
        # Cerramos la sesión siempre, haya error o no
        db.close()
