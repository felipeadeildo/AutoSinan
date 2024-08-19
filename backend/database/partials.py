from prisma.models import User

User.create_partial("UserCreate", exclude={"id", "role"})
User.create_partial("UserSafe", exclude={"password", "roleId"})
