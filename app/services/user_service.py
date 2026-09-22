"""Reglas de negocio relacionadas con usuarios."""

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Coordina los casos de uso y sus reglas de negocio."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_all(self) -> list[User]:
        """Devuelve todos los usuarios disponibles."""

        return self.repository.get_all()

    def get_by_id(self, user_id: int) -> User:
        """Devuelve un usuario o transforma su ausencia en un error HTTP 404."""

        user = self.repository.get_by_id(user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        return user
