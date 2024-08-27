from typing import List, Optional

from prisma.enums import ConfigType
from prisma.partials import BotConfigOptionSafe
from pydantic import BaseModel, field_validator


class BotConfiguration(BaseModel):
    key: str
    value: str
    name: str
    desc: Optional[str] = None
    type: ConfigType
    options: Optional[List[BotConfigOptionSafe]] = None

    @field_validator("options")
    def validate_options(cls, value):
        if len(value) == 0:
            return None
        return value
