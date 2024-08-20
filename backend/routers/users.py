from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from prisma.models import User
from prisma.partials import UserCreate, UserSafe
from services.auth import get_current_user, get_password_hash, permission_required

router = APIRouter()


@router.post(
    "",
    summary="Register",
    response_model=User,
    description="Register a new user",
)
@permission_required("users:create")
async def create_user(user: UserCreate):
    user_exists = await User.prisma().find_unique(where={"username": user.username})
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered"
        )
    hashed_password = get_password_hash(user.password)
    # TODO: find the role and check if it exists
    new_user = await User.prisma().create(
        data={
            "name": user.name,
            "username": user.username,
            "password": hashed_password,
            "roleId": user.roleId,
        }
    )

    return new_user


@router.get(
    "",
    summary="Get All Users",
    response_model=List[UserSafe],
    description="Get all users data",
)
@permission_required("users:read")
async def list_users(current_user: Annotated[User, Depends(get_current_user)]):
    return await User.prisma().find_many()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@permission_required("users:delete")
async def delete_user(
    user_id: str, current_user: Annotated[User, Depends(get_current_user)]
):
    await User.prisma().delete(where={"id": user_id})


@router.put("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@permission_required("users:update")
async def update_user(
    user_id: str,
    user: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    await User.prisma().update(
        where={"id": user_id}, data={"name": user.name, "username": user.username}
    )
