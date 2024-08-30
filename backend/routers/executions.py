from typing import List

from fastapi import APIRouter, Depends
from prisma.models import User
from prisma.partials import ExecSafe
from services.auth import get_current_user, permission_required

router = APIRouter()


@router.get("", response_model=List[ExecSafe])
@permission_required("executions:read")
def get_executions(current_user: User = Depends(get_current_user)):
    return ExecSafe.prisma().find_many(
        where={"userId": current_user.id}, order={"startTime": "desc"}
    )
