from typing import Callable, Mapping

from prisma.enums import ConfigValueType
from prisma.models import BotConfiguration
from pydantic import field_serializer


@field_serializer("value")
def bot_configuration_serializer(self, value: str):
    casters: Mapping[ConfigValueType, Callable] = {
        ConfigValueType.INT: int,
        ConfigValueType.FLOAT: float,
        ConfigValueType.STRING: str,
        ConfigValueType.BOOLEAN: lambda x: x.lower() == "true",
    }

    caster = casters.get(self.type, lambda x: x)
    return caster(value)


async def setup():
    setattr(BotConfiguration, "serializer", bot_configuration_serializer)
