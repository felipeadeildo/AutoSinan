from datetime import datetime
from typing import List

from config import BOTS
from prisma.models import Bot, BotConfigOption, DefaultBotConfig


async def setup():
    for bot, configs in BOTS:
        bot_instance = await Bot.prisma().find_unique(where={"slug": bot["slug"]})

        if bot_instance is None:
            bot_instance = await Bot.prisma().create(data=bot)
        else:
            await Bot.prisma().update(
                where={"slug": bot["slug"]},
                data={
                    "name": bot["name"],
                    "desc": bot["desc"],
                    "version": bot["version"],
                    "status": bot["status"],
                    "updatedAt": bot.get("updatedAt", datetime.now()),
                },
            )

        await update_default_configurations(bot_instance.id, configs)


async def update_default_configurations(bot_id: str, configs: List[dict]):
    """
    Updates the default configurations for the given bot.

    Args:
        bot_id (str): The ID of the bot to update.
        configs (List[dict]): The new default configurations.
    """

    await BotConfigOption.prisma().delete_many(
        where={"config": {"is": {"botId": bot_id}}}
    )

    await DefaultBotConfig.prisma().delete_many(where={"botId": bot_id})

    # Reinsere as configurações padrão fornecidas
    for config in configs:
        options = config.pop("options", [])
        await DefaultBotConfig.prisma().create(
            data={  # type: ignore
                "botId": bot_id,
                **config,
                **({"options": {"create": options}} if options else {}),
            }
        )
