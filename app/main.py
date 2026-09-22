"""Punto de entrada de la API."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

# Importar el modelo hace que SQLAlchemy lo registre en Base.metadata antes de
# crear las tablas. No es necesario usar User directamente en este archivo.
import app.models.user  # noqa: F401
from app.database import Base, engine
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Ejecuta las tareas de inicio y cierre de la aplicacion."""

    # Para este ejemplo educativo creamos las tablas que aun no existan.
    # En proyectos reales se recomienda usar migraciones con Alembic.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API de Usuarios",
    description="Ejemplo de arquitectura por capas con FastAPI y SQLAlchemy.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users_router)


@app.get("/", tags=["General"])
def root() -> dict[str, str]:
    """Confirma que la API esta disponible y orienta hacia Swagger UI."""

    return {
        "message": "API de Usuarios funcionando",
        "documentation": "/docs",
    }
