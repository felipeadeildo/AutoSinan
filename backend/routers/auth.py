from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from models.auth import Token
from prisma.models import User
from prisma.partials import UserSafe
from services.auth import create_access_token, get_current_user, verify_password

router = APIRouter()


@router.post(
    "/login",
    summary="Login",
    response_model=Token,
    description="Login with username and password",
)
async def login(
    response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await User.prisma().find_unique(where={"username": form_data.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect username or password",
        )
    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": user.id})

    response.set_cookie(
        key="access_token", value=access_token, httponly=True, secure=True
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me",
    summary="Get Current User",
    response_model=UserSafe,
    description="Get current user data",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get(
    "/refresh-token",
    tags=["Auth"],
    summary="Refresh Token",
    response_model=Token,
    description="Refresh token",
)
async def refresh_token(
    response: Response, current_user: User = Depends(get_current_user)
):
    access_token = create_access_token(data={"sub": current_user.id})
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, secure=True
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/logout",
    tags=["Auth"],
    summary="Logout",
    description="Delete access token",
)
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    response.delete_cookie(key="access_token", httponly=True, secure=True)
    return {"message": "Deslogado com sucesso!"}
