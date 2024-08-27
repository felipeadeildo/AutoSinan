from typing import List

from fastapi import APIRouter, Depends, HTTPException
from models.bot import BotConfiguration
from prisma.models import Bot, BotConfig, DefaultBotConfig, User
from prisma.partials import BotConfigUpdate
from services.auth import get_current_user, permission_required

router = APIRouter()


@router.get("/{bot_slug}", response_model=List[BotConfiguration])
@permission_required("bots:read")
async def get_bot_configurations(
    bot_slug: str, current_user: User = Depends(get_current_user)
):
    bot = await Bot.prisma().find_unique(where={"slug": bot_slug})
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")

    existing_configs = await BotConfig.prisma().find_many(
        where={"botId": bot.id, "userId": current_user.id},
        order={"key": "desc"},
    )

    if not existing_configs:
        default_configs = await DefaultBotConfig.prisma().find_many(
            where={"botId": bot.id}, include={"options": True}
        )

        for default_config in default_configs:
            await BotConfig.prisma().create(
                data={
                    "botId": bot.id,
                    "userId": current_user.id,
                    "key": default_config.key,
                    "value": "",
                }
            )

        existing_configs = await BotConfig.prisma().find_many(
            where={"botId": bot.id, "userId": current_user.id},
            include={"bot": {"include": {"configs": True}}},
        )

    dumped_configs = []
    for config in existing_configs:
        default_config = await DefaultBotConfig.prisma().find_first(
            where={"key": config.key, "botId": bot.id}, include={"options": True}
        )

        dumped = config.model_dump()
        if default_config is not None:
            dumped.update(default_config.model_dump())

        dumped_configs.append(dumped)

    return dumped_configs


@router.put("/{bot_slug}")
@permission_required("bots:read")  # yes, it's a read
async def update_bot_configuration(
    bot_slug: str,
    config: BotConfigUpdate,
    current_user: User = Depends(get_current_user),
):
    bot = await Bot.prisma().find_unique(where={"slug": bot_slug})
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")

    config_exists = await BotConfig.prisma().find_first(
        where={"botId": bot.id, "key": config.key, "userId": current_user.id}
    )
    if not config_exists:
        raise HTTPException(status_code=404, detail="Configuration not found")

    await BotConfig.prisma().update(
        where={"id": config_exists.id},
        data={"value": config.value},
    )
