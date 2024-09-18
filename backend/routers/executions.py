import shutil
from pathlib import Path
from typing import List

from config import settings
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from prisma.models import Bot, Exec, ExecFile, User
from prisma.partials import ExecFileSafe, ExecSafe
from services.auth import get_current_user, permission_required

router = APIRouter()


@router.get("", response_model=List[ExecSafe])
@permission_required("executions:read")
async def get_executions(current_user: User = Depends(get_current_user)):
    return await ExecSafe.prisma().find_many(
        where={"userId": current_user.id}, order={"startTime": "desc"}
    )


@router.post("/{bot_slug}", response_model=ExecSafe)
@permission_required("executions:create")
async def create_execution(
    bot_slug: str, current_user: User = Depends(get_current_user)
):
    bot = await Bot.prisma().find_unique(where={"slug": bot_slug})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    execution = await Exec.prisma().create({"botId": bot.id, "userId": current_user.id})

    return execution


@router.post("/{exec_id}/upload", response_model=ExecFileSafe)
async def upload_file(
    exec_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    execution = await Exec.prisma().find_unique(where={"id": exec_id})

    if not execution or execution.userId != current_user.id:
        raise HTTPException(status_code=404, detail="Execution not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file name")

    # TODO: given a hashed filename to file_path instead of the original filename
    file_path = settings.UPLOADED_FILES_DEST / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return ExecFile.prisma().create(
        {"execId": exec_id, "filePath": str(file_path), "fileName": file.filename}
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_file(file_id: str, current_user: User = Depends(get_current_user)):
    exec_file = await ExecFile.prisma().find_unique(
        where={"id": file_id}, include={"exec": True}
    )
    if (
        exec_file is None
        or not exec_file.exec
        or exec_file.exec.userId != current_user.id
    ):
        raise HTTPException(status_code=404, detail="File not found")

    # TODO: when using hashed filename, construct the hash again (using the metadata of the file) and construct the path based on the settings uploaded_files_dest and the hash
    file_path = Path(exec_file.filePath)
    file_path.unlink(missing_ok=True)

    await ExecFile.prisma().delete(where={"id": file_id})
