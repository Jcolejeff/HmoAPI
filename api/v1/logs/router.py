from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import schemas as comment_schemas
from .services import LogService
from api.db.database import get_db
from api.core.dependencies.user import is_authenticated
from api.v1.user.schemas import ShowUser
from fastapi import BackgroundTasks
from api.utils import paginator
from datetime import datetime

from api.v1.logs.services import LogService
from api.v1.logs.schemas import LogBase, LogAction

app = APIRouter(tags=["Logs"])


# @app.get("/logs", status_code=status.HTTP_200_OK)
# async def get_logs(
#     id: int,
#     entity: str,
#     user: ShowUser = Depends(is_authenticated),
#     db: Session = Depends(get_db),
#     size: int = 20,
#     page: int = 1,
# ):

#     logs = await LogService.fetch_all(id=id, entity=entity)

#     return logs
