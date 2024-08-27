from prisma.models import Bot, BotConfig, BotConfigOption, DefaultBotConfig, User

# TODO: refatorar estes partials (tem coisa demais sendo retornada na API)

User.create_partial("UserCreate", exclude={"id", "role"})
User.create_partial(
    "UserSafe", exclude={"password", "roleId", "subs", "configs", "executions"}
)
User.create_partial("UserDetail", exclude={"password", "configs", "executions", "subs"})

# Partials for Bot model
Bot.create_partial("BotSafe", exclude={"execs", "interrupts", "tasks", "benefits"})

Bot.create_partial(
    "BotDetail",
    include={
        "id": True,
        "name": True,
        "desc": True,
        "version": True,
        "status": True,
        "slug": True,
        "updatedAt": True,
        "configs": {"select": {"key": True, "value": True, "type": True}},
        "defaults": {
            "select": {
                "key": True,
                "name": True,
                "desc": True,
                "type": True,
                "options": {"select": {"key": True, "value": True}},
            }
        },
    },
)

# Partials for BotConfig model
BotConfig.create_partial(
    "BotConfigSafe",
    include={"key": True, "value": True},
)

BotConfig.create_partial(
    "BotConfigUpdate", exclude={"id", "botId", "userId", "user", "bot"}
)

# Partials for DefaultBotConfig model
DefaultBotConfig.create_partial(
    "DefaultConfigSafe",
    include={
        "key": True,
        "name": True,
        "desc": True,
        "type": True,
        "options": {"select": {"key": True, "value": True}},
    },
)

# Partials for BotConfigOption model
BotConfigOption.create_partial(
    "BotConfigOptionSafe", include={"key": True, "value": True}
)
