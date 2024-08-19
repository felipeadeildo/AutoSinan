from functools import wraps
from typing import Annotated, Any, Callable

from database.db import db
from fastapi import Depends, HTTPException
from prisma.models import User
from services.auth.oauth2 import get_current_user


def permission_required(permission: str) -> Callable:
    """Decorator to enforce permission checks on a route.

    Args:
        permission (str): The required permission to access the route.

    Returns:
        Callable: The wrapped function with the permission check applied.

    Raises:
        HTTPException: If the user does not have the required permission.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args: Any,
            current_user: Annotated[User, Depends(get_current_user)],
            **kwargs: Any,
        ) -> Any:
            role = current_user.role
            if role is None:
                raise HTTPException(status_code=403, detail="Operation not permitted")

            if permission not in [perm.name for perm in role.permissions or []]:
                raise HTTPException(status_code=403, detail="Operation not permitted")

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


# TODO: test this feature.
async def resource_owner_required(
    resource_model: str,
    resource_identification: str,
    resource_identifier_column: str = "id",
    resource_owner_column: str = "user_id",
    user: User = Depends(get_current_user),
):
    """Ensures that the current user is the owner of the resource.

    Args:
        resource_model (str): The name of the resource model in the database.
        resource_identification (str): The identifier of the resource (e.g., resource ID).
        resource_identifier_column (str, optional): The column name for the resource ID. Defaults to "id".
        resource_owner_column (str, optional): The column name for the resource owner. Defaults to "user_id".
        user (User): The current authenticated user, provided by the dependency.

    Returns:
        Any: The resource if the user is the owner.

    Raises:
        HTTPException: If the resource is not found or the user is not the owner.
    """
    resource_query = getattr(db, resource_model)

    forbidden_raise = HTTPException(
        status_code=403,
        detail=f"Resource '{resource_model}' not found or you do not have access to it",
    )

    if resource_query is None:
        raise HTTPException(
            status_code=500,
            detail=f"Resource {resource_model} is not defined. Contact support.",
        )

    try:
        resource = await resource_query.find_first(
            where={
                resource_identifier_column: resource_identification,
                resource_owner_column: user.id,
            }
        )
    except Exception:
        raise forbidden_raise

    if resource is None:
        raise forbidden_raise

    return resource
