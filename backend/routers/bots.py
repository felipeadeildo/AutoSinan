from typing import Annotated, List

from fastapi import APIRouter, Depends
from prisma.models import Bot, User
from prisma.partials import BotSafe
from services.auth import get_current_user, permission_required

router = APIRouter()

# Dado que os bots são criados a partir de constantes, não há necessidade de criar rotas além das de visualização.
# Em algum momento futuro, pode ser necessário uma rota para update (put) somente para alterar status do bot (active, paused, deprecated) e informações como descrição e nome. Demais informações não serão alteradas.


@router.get(
    "",
    response_model=List[BotSafe],
    summary="Get all the bots",
    description="Get all the bots informations as name and needed informations",
)
@permission_required("bots:read")
async def list_bots(current_user: Annotated[User, Depends(get_current_user)]):
    return await Bot.prisma().find_many()
