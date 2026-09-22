from fastapi import HTTPException

from app.models.user import User


class UserService:

    def __init__(self, repository):
        self.repository = repository

    def get_all(self):

        return self.repository.get_all()

    def get_by_id(self, user_id: int):

        user = self.repository.get_by_id(
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        return user