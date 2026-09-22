"""Operaciones de persistencia relacionadas con usuarios."""

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Aisla las consultas SQLAlchemy del resto de la aplicacion."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[User]:
        """Obtiene todos los usuarios."""

        return self.db.query(User).all()

    def get_by_id(self, user_id: int) -> User | None:
        """Obtiene un usuario por su clave primaria."""

        return self.db.get(User, user_id)
