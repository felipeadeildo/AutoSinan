from prisma.models import Bot, User

User.create_partial("UserCreate", exclude={"id", "role"})
User.create_partial("UserSafe", exclude={"password", "roleId"})

Bot.create_partial(
    "BotSafe", exclude={"executions", "interruptions", "tasks", "planBenefits"}
)
