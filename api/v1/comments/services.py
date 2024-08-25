from sqlalchemy.orm import Session
from datetime import datetime
from typing import Any
from api.core.base.services import Service
from .exceptions import CommentNotFoundException, NotAuthorizedException, ReferencedRecordNotFound, ParentCommentNotFoundException
from .models import Comment
from .schemas import CommentCreate, CommentUpdate, EntityNameEnum
from api.utils.utils import does_referenced_record_exist

class CommentService(Service):
    def __init__(self) -> None:
        pass

    @classmethod
    async def create(cls, payload: CommentCreate, created_by: int, db: Session):

        does_referenced_record_exist(table_name=payload.table_name, record_id=payload.record_id, db=db)

        if payload.parent_id:
            try:
                await cls.fetch(db=db, id=payload.parent_id)
            except CommentNotFoundException:
                raise ParentCommentNotFoundException()

        db_comment = Comment(
            content=payload.content,
            author=created_by,
            table_name=payload.table_name.value,
            record_id=payload.record_id,
            parent_id=payload.parent_id,
            organization_id=payload.organization_id
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)

        return db_comment

    @classmethod
    async def fetch(cls, db: Session, id: int):
        comment = db.query(Comment).filter(Comment.id == id).first()

        if not comment:
            raise CommentNotFoundException()

        return comment

    @classmethod
    async def fetch_all(cls, 
                        db: Session, 
                        table_name: EntityNameEnum, 
                        organization_id: int, 
                        record_id: int, 
                        size: int, 
                        offset: int, 
                        parent_id: int = None
                    ):
        
        does_referenced_record_exist(table_name=table_name, record_id=record_id, db=db)

        query = db.query(Comment).filter(
            Comment.table_name == table_name.value, 
            Comment.record_id == record_id, 
            Comment.organization_id == organization_id
            )

        if parent_id:
            query = query.filter(Comment.parent_id == parent_id)

        count = query.count()
        comments = query.order_by(Comment.date_created.desc()).offset(offset=offset).limit(limit=size).all()

        return (comments, count)

    @classmethod
    async def update(cls, db: Session, comment_id: int, payload: CommentUpdate, author_id: int):
        db_comment = await cls.fetch(db, comment_id)

        if not db_comment:
            raise CommentNotFoundException()

        if db_comment.author != author_id:
            raise NotAuthorizedException()

        if payload.content is not None:
            db_comment.content = payload.content

        db_comment.last_updated = datetime.now()
        db_comment.is_edited = True

        db.commit()
        db.refresh(db_comment)

        return db_comment

    @classmethod
    async def delete(cls, db: Session, comment_id: int, author_id: int):
        db_comment = await cls.fetch(db, comment_id)

        if db_comment.author != author_id:
            raise NotAuthorizedException()

        db.delete(db_comment)
        db.commit()
 
        return "Success"
