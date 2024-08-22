from .bots import setup as setup_bots
from .roles import setup as setup_roles


async def setup():
    await setup_bots()
    await setup_roles()
