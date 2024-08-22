from datetime import datetime
from typing import List, Literal, Mapping

from prisma.enums import BotStatus
from prisma.types import BotCreateInput

BOTS: List[BotCreateInput] = [
    {
        "name": "Investigador",
        "description": "Dado os resultados de exames do GAL, pesquisa pelos pacientes em questão e aplica a investigação.",
        "version": "0.1.0",
        "status": BotStatus.ACTIVE,
        "slug": "investigator",
        "lastUpdated": datetime(2024, 8, 22, 15, 30),
    }
]
"""List of bots that will be created in the database and can be used in the app."""

ROLES: Mapping[Literal["admin", "user"], List[str]] = {
    "admin": [
        "users:create",
        "users:read",
        "users:update",
        "users:delete",
        "bots:read",
    ],
    "user": ["users:read", "bots:read"],
}
"""Roles that will be used in the app and permissions to access some routes."""
