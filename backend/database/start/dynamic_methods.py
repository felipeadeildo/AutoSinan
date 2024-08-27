from typing import Callable, Mapping

from prisma.enums import ConfigType
from prisma.models import BotConfig
from pydantic import field_serializer


@field_serializer("value")
def bot_config_serializer(self, value: str):
    casters: Mapping[ConfigType, Callable] = {
        ConfigType.INT: int,
        ConfigType.FLOAT: float,
        ConfigType.STRING: str,
        ConfigType.BOOLEAN: lambda x: x.lower() == "true",
    }

    caster = casters.get(self.type, lambda x: x)
    return caster(value)


async def setup():
    setattr(BotConfig, "serializer", bot_config_serializer)
