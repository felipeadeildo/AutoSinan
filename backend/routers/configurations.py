from typing import List

from fastapi import APIRouter, Depends, HTTPException
from prisma.enums import ConfigValueType
from prisma.models import Bot, BotConfiguration, User
from prisma.partials import BotConfigurationSafe
from services.auth import get_current_user, permission_required

router = APIRouter()


@router.get("/{bot_slug}", response_model=List[BotConfigurationSafe])
@permission_required("bots:read")
async def get_bot_configurations(
    bot_slug: str, current_user: User = Depends(get_current_user)
):
    bot = await Bot.prisma().find_unique(where={"slug": bot_slug})
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")

    return await BotConfiguration.prisma().find_many(
        where={"botId": bot.id, "userId": current_user.id}
    )


@router.put("/{bot_slug}")
@permission_required("bots:read")  # yes, it's a read
async def update_bot_configuration(
    bot_slug: str,
    key: str,
    value: str,
    type: ConfigValueType,
    current_user: User = Depends(get_current_user),
):
    bot = await Bot.prisma().find_unique(where={"slug": bot_slug})
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")

    config_exists = await BotConfiguration.prisma().find_first(
        where={"botId": bot.id, "key": key, "userId": current_user.id}
    )
    if config_exists:
        await BotConfiguration.prisma().update(
            where={"id": config_exists.id},
            data={"value": value},
        )
    else:
        await BotConfiguration.prisma().create(
            data={
                "botId": bot.id,
                "key": key,
                "value": value,
                "userId": current_user.id,
                "type": type,
            }
        )
