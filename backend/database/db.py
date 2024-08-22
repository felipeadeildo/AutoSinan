from database.start import setup
from prisma import Prisma

db = Prisma(auto_register=True)


async def startup() -> None:
    await db.connect()
    await setup()


async def shutdown() -> None:
    await db.disconnect()
