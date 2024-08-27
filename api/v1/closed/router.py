from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from . import schemas as closed_schemas
from .services import ClosedService
from api.db.database import get_db
from api.core.dependencies.user import is_authenticated
from api.v1.user.schemas import ShowUser
from fastapi import BackgroundTasks
from api.utils import paginator

app = APIRouter(tags=["Closeds"])


@app.post("/closeds", status_code=status.HTTP_201_CREATED, response_model=closed_schemas.ShowClosed)
async def create_closed(
    payload: closed_schemas.ClosedCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: ShowUser = Depends(is_authenticated)
):

    closed = await ClosedService.create(payload=payload, created_by=user.id, db=db)

    # Create log entry
    # log_payload = {
    #     "name": f"{user.first_name} {user.last_name}",
    #     "action": LogAction.CREATED.value,
    #     "message": f"new Closed {closed.id}",
    #     "date": datetime.now(),
    #     "entity": "asset",
    #     "entity_id": closed.id,
    # }

    # background_tasks.add_task(LogService.create, log_payload)

    return closed_schemas.ShowClosed.model_validate(closed)


@app.get("/closeds/{closed_id}", status_code=status.HTTP_200_OK, response_model=closed_schemas.ShowClosed)
async def get_closed(closed_id: int, db: Session = Depends(get_db)):

    closed = await ClosedService.fetch(db=db, id=closed_id)

    return closed_schemas.ShowClosed.model_validate(closed)


@app.get("/closeds", status_code=status.HTTP_200_OK, response_model=closed_schemas.PaginatedClosedsResponse)
async def get_closeds(
   
    organization_id: int,
    
    user: ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
    size: int = 20,
    page: int = 1,
):

    page_size = 20 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    closeds, total = await ClosedService.fetch_all(db=db,
                                                   
                                                     organization_id=organization_id,
                                                    
                                                   
                                                     offset=offset,
                                                     size=page_size)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint='/closeds',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map(
            (lambda closeds: closed_schemas.ShowClosed.model_validate(closeds)), closeds))
    )

    return response


@app.put("/closeds/{closed_id}", response_model=closed_schemas.ShowClosed)
async def update_closed(
    closed_id: int,
    payload: closed_schemas.ClosedUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: ShowUser = Depends(is_authenticated)
):
    db_closed = await ClosedService.update(db=db, closed_id=closed_id,
                                             payload=payload, author_id=user.id)

    # Create log entry for update
    # changes = []

    # if payload.content:
    #     changes.append(f"Closed updated to '{payload.content}'")

    # if len(changes) > 0:
    #     log_payload = {
    #         "name": f"{user.first_name} {user.last_name}",
    #         "action": LogAction.UPDATED.value,
    #         "message": f"the asset {db_closed.id}. Changes: " + ", ".join(changes),
    #         "date": datetime.now(),
    #         "entity": "asset",
    #         "entity_id": db_closed.id,
    #     }

    #     background_tasks.add_task(LogService.create, log_payload)

    return closed_schemas.ShowClosed.model_validate(db_closed)


@app.delete("/closeds/{closed_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_closed(
    closed_id: int,
    db: Session = Depends(get_db),
    user: ShowUser = Depends(is_authenticated)
):
    result = await ClosedService.delete(db=db,
                                         closed_id=closed_id,
                                         author_id=user.id)

    return {"detail": "Closed deleted successfully"}
