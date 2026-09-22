from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserResponse
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def get_service(
    db: Session = Depends(get_db)
):

    repository = UserRepository(db)

    return UserService(repository)


@router.get(
    "/",
    response_model=list[UserResponse]
)
def get_users(
    service: UserService = Depends(get_service)
):

    return service.get_all()


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(
    user_id: int,
    service: UserService = Depends(get_service)
):

    return service.get_by_id(user_id)