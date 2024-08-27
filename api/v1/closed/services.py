from sqlalchemy.orm import Session
from datetime import datetime
from typing import Any
from api.core.base.services import Service
from .exceptions import ClosedNotFoundException, NotAuthorizedException, ReferencedRecordNotFound, ParentClosedNotFoundException
from .models import Closed
from .schemas import ClosedCreate, ClosedUpdate
from api.utils.utils import does_referenced_record_exist

class ClosedService(Service):
    def __init__(self) -> None:
        pass

    @classmethod
    async def create(cls, payload: ClosedCreate, created_by: int, db: Session):

        

       

        db_closed = Closed(
            content=payload.content,
            author=created_by,
        
            organization_id=payload.organization_id
        )
        db.add(db_closed)
        db.commit()
        db.refresh(db_closed)

        return db_closed

    @classmethod
    async def fetch(cls, db: Session, id: int):
        closed = db.query(Closed).filter(Closed.id == id).first()

        if not closed:
            raise ClosedNotFoundException()

        return closed

    @classmethod
    async def fetch_all(cls, 
                        db: Session, 
                      
                        organization_id: int, 
                        
                        size: int, 
                        offset: int, 
                       
                    ):
        
        query = db.query(Closed).filter(
            
            Closed.organization_id == organization_id
            )

      

        count = query.count()
        closeds = query.order_by(Closed.date_created.desc()).offset(offset=offset).limit(limit=size).all()

        return (closeds, count)

    @classmethod
    async def update(cls, db: Session, closed_id: int, payload: ClosedUpdate, author_id: int):
        db_closed = await cls.fetch(db, closed_id)

        if not db_closed:
            raise ClosedNotFoundException()

        if db_closed.author != author_id:
            raise NotAuthorizedException()

        if payload.content is not None:
            db_closed.content = payload.content

        db_closed.last_updated = datetime.now()
        db_closed.is_edited = True

        db.commit()
        db.refresh(db_closed)

        return db_closed

    @classmethod
    async def delete(cls, db: Session, closed_id: int, author_id: int):
        db_closed = await cls.fetch(db, closed_id)

        if db_closed.author != author_id:
            raise NotAuthorizedException()

        db.delete(db_closed)
        db.commit()
 
        return "Success"
