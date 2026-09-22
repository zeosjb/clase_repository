"""Configuracion de SQLAlchemy y dependencia de sesion de la API."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = "sqlite:///./database.db"

# SQLite limita, por defecto, cada conexion al hilo que la creo. FastAPI puede
# atender una misma peticion desde distintos hilos, por eso se desactiva esa
# comprobacion exclusivamente para SQLite.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Fabrica de sesiones. Una Session representa una unidad de trabajo con la BD.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos de la aplicacion."""


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesion por peticion y garantiza que siempre se cierre."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
