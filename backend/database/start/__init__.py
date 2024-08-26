from .bots import setup as setup_bots
from .dynamic_methods import setup as setup_dynamic_methods
from .roles import setup as setup_roles


async def setup():
    await setup_bots()
    await setup_roles()
    await setup_dynamic_methods()
