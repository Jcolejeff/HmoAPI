from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from . import schemas as comment_schemas
from .services import CommentService
from api.db.database import get_db
from api.core.dependencies.user import is_authenticated
from api.v1.user.schemas import ShowUser
from fastapi import BackgroundTasks
from api.utils import paginator

app = APIRouter(tags=["Comments"])


@app.post("/comments", status_code=status.HTTP_201_CREATED, response_model=comment_schemas.ShowComment)
async def create_comment(
    payload: comment_schemas.CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: ShowUser = Depends(is_authenticated)
):

    comment = await CommentService.create(payload=payload, created_by=user.id, db=db)

    # Create log entry
    # log_payload = {
    #     "name": f"{user.first_name} {user.last_name}",
    #     "action": LogAction.CREATED.value,
    #     "message": f"new Comment {comment.id}",
    #     "date": datetime.now(),
    #     "entity": "asset",
    #     "entity_id": comment.id,
    # }

    # background_tasks.add_task(LogService.create, log_payload)

    return comment_schemas.ShowComment.model_validate(comment)


@app.get("/comments/{comment_id}", status_code=status.HTTP_200_OK, response_model=comment_schemas.ShowComment)
async def get_comment(comment_id: int, db: Session = Depends(get_db)):

    comment = await CommentService.fetch(db=db, id=comment_id)

    return comment_schemas.ShowComment.model_validate(comment)


@app.get("/comments", status_code=status.HTTP_200_OK, response_model=comment_schemas.PaginatedCommentsResponse)
async def get_comments(
    table_name: comment_schemas.EntityNameEnum,
    record_id: int,
    organization_id: int,
    parent_id: int = None,
    user: ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
    size: int = 20,
    page: int = 1,
):

    page_size = 20 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    comments, total = await CommentService.fetch_all(db=db,
                                                     table_name=table_name,
                                                     organization_id=organization_id,
                                                     record_id=record_id,
                                                     parent_id=parent_id,
                                                     offset=offset,
                                                     size=page_size)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint='/comments',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map(
            (lambda comments: comment_schemas.ShowComment.model_validate(comments)), comments))
    )

    return response


@app.put("/comments/{comment_id}", response_model=comment_schemas.ShowComment)
async def update_comment(
    comment_id: int,
    payload: comment_schemas.CommentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: ShowUser = Depends(is_authenticated)
):
    db_comment = await CommentService.update(db=db, comment_id=comment_id,
                                             payload=payload, author_id=user.id)

    # Create log entry for update
    # changes = []

    # if payload.content:
    #     changes.append(f"Comment updated to '{payload.content}'")

    # if len(changes) > 0:
    #     log_payload = {
    #         "name": f"{user.first_name} {user.last_name}",
    #         "action": LogAction.UPDATED.value,
    #         "message": f"the asset {db_comment.id}. Changes: " + ", ".join(changes),
    #         "date": datetime.now(),
    #         "entity": "asset",
    #         "entity_id": db_comment.id,
    #     }

    #     background_tasks.add_task(LogService.create, log_payload)

    return comment_schemas.ShowComment.model_validate(db_comment)


@app.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: ShowUser = Depends(is_authenticated)
):
    result = await CommentService.delete(db=db,
                                         comment_id=comment_id,
                                         author_id=user.id)

    return {"detail": "Comment deleted successfully"}
