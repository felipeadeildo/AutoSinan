from config import settings
from prisma import Prisma
from prisma.models import Role, User
from services.auth import get_password_hash

db = Prisma(auto_register=True)

ROLES = {
    "admin": ["users:create", "users:read", "users:update", "users:delete"],
    "user": ["users:read"],
}


async def startup() -> None:
    await db.connect()

    for role in ["admin", "user"]:
        role_exists = await Role.prisma().find_unique(where={"name": role})
        if role_exists is None:
            await Role.prisma().create(data={"name": role})

    admin_role = await Role.prisma().find_unique(where={"name": "admin"})

    user_exists = await User.prisma().find_unique(
        where={"username": settings.DEFAULT_ADMIN_USERNAME}
    )
    if user_exists is None:
        await User.prisma().create(
            data={
                "username": settings.DEFAULT_ADMIN_USERNAME,
                "name": settings.DEFAULT_ADMIN_NAME,
                "password": get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                "roleId": getattr(admin_role, "id"),
            }
        )


async def shutdown() -> None:
    await db.disconnect()
