from datetime import datetime

from config import BOTS
from prisma.models import Bot


async def setup():
    for bot in BOTS:
        bot_exists = await Bot.prisma().find_unique(where={"name": bot["name"]})
        if bot_exists is None:
            await Bot.prisma().create(data=bot)
        else:
            await Bot.prisma().update(
                where={"name": bot["name"]},
                data={
                    "description": bot["description"],
                    "version": bot["version"],
                    "status": bot["status"],
                    "lastUpdated": bot.get("lastUpdated", datetime.now()),
                },
            )
