from typing import Mapping

from config import ROLES, settings
from prisma.models import Permission, Role, User
from services.auth import get_password_hash


async def setup():
    permission_instances: Mapping[str, Permission] = {}
    for permission in set(perm for perm in sum(ROLES.values(), [])):
        permission_instance = await Permission.prisma().find_unique(
            where={"name": permission}
        )
        if not permission_instance:
            permission_instance = await Permission.prisma().create(
                data={"name": permission},
            )
        permission_instances[permission] = permission_instance

    for role, permissions in ROLES.items():
        role_instance = await Role.prisma().find_unique(where={"name": role})
        if not role_instance:
            role_instance = await Role.prisma().create(
                data={"name": role},
            )

        await Role.prisma().update(
            where={"id": role_instance.id},
            data={
                "permissions": {
                    "set": [
                        {"id": permission_instances[perm].id} for perm in permissions
                    ]
                }
            },
        )

    admin_role = await Role.prisma().find_unique(where={"name": "admin"})
    if admin_role:
        user_exists = await User.prisma().find_unique(
            where={"username": settings.DEFAULT_ADMIN_USERNAME}
        )
        if user_exists is None:
            await User.prisma().create(
                data={
                    "username": settings.DEFAULT_ADMIN_USERNAME,
                    "name": settings.DEFAULT_ADMIN_NAME,
                    "password": get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                    "roleId": admin_role.id,
                }
            )
