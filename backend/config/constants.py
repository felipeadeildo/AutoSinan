from datetime import datetime
from typing import List, Literal, Mapping, Tuple

from prisma.enums import BotStatus, ConfigType
from prisma.types import BotCreateInput

BOTS: List[Tuple[BotCreateInput, List[dict[str, object]]]] = [
    (
        {
            "name": "Investigador",
            "desc": "Dado os resultados de exames do GAL, pesquisa pelos pacientes em questão e aplica a investigação.",
            "version": "0.1.0",
            "status": BotStatus.ACTIVE,
            "slug": "investigator",
            "updatedAt": datetime(2024, 8, 22, 15, 30),
        },
        [
            {
                "key": "sinan_username",
                "name": "Usuário do Sinan",
                "desc": "Nome de usuário para acessar o Sinan Online.",
                "type": ConfigType.STRING,
            },
            {
                "key": "sinan_password",
                "name": "Senha do Sinan",
                "desc": "Senha para acessar o Sinan Online.",
                "type": ConfigType.STRING,
            },
            {
                "key": "agravo",
                "name": "Agravo utilizado",
                "desc": "Escolha qual agravo será utilizado na investigação.",
                "type": ConfigType.STRING,
                "options": [
                    {"key": agravo, "value": agravo}
                    for agravo in ["A90 - DENGUE", "A92.0 - FEBRE DE CHIKUNGUNYA"]
                ],
            },
            {
                "key": "municipio",
                "name": "Município",
                "desc": "Município onde o bot está rodando.",
                "type": ConfigType.STRING,
                "options": [{"key": "Florianópolis", "value": "FLORIANOPOLIS"}],
            },
            {
                "key": "criterio_nome_do_paciente",
                "name": "Critério de Pesquisa: Nome do paciente",
                "desc": "Critério de pesquisa para Nome do paciente.",
                "type": ConfigType.STRING,
                "options": [
                    {"key": op, "value": op}
                    for op in ["Igual", "Contendo", "Iniciando em", "NÃO USAR CRITÉRIO"]
                ],
            },
            {
                "key": "criterio_nome_da_mae",
                "name": "Critério de Pesquisa: Nome da mãe",
                "desc": "Critério de pesquisa para Nome da mãe.",
                "type": ConfigType.STRING,
                "options": [
                    {"key": op, "value": op}
                    for op in ["Igual", "Contendo", "Iniciando em", "NÃO USAR CRITÉRIO"]
                ],
            },
            {
                "key": "criterio_data_de_nascimento",
                "name": "Critério de Pesquisa: Data de nascimento",
                "desc": "Critério de pesquisa para Data de nascimento.",
                "type": ConfigType.STRING,
                "options": [
                    {"key": op, "value": op}
                    for op in [
                        "Igual",
                        "Diferente",
                        "Maior",
                        "Menor",
                        "Maior ou igual",
                        "Menor ou igual",
                        "Não USAR CRITÉRIO",
                    ]
                ],
            },
        ],
    ),
]
"""List of bots that will be created in the database and can be used in the app."""

ROLES: Mapping[Literal["admin", "user"], List[str]] = {
    "admin": [
        "users:create",
        "users:read",
        "users:update",
        "users:delete",
        "bots:read",
        "executions:read",
        "executions:create",
        "executions:update",
    ],
    "user": [
        "users:read",
        "bots:read",
        "executions:read",
        "executions:create",
        "executions:update",
    ],
}
"""Roles that will be used in the app and permissions to access some routes."""
