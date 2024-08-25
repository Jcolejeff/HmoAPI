from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from api.core.base.constants import EntityNameEnum, table_name_to_model_map
from api.core.base.exceptions import ReferencedRecordNotFound

def build_paginated_response(
    page: int, size: int, total: int, pointers: dict, items
) -> dict:
    response = {
        "page": page,
        "size": size,
        "total": total,
        "previous_page": pointers["previous"],
        "next_page": pointers["next"],
        "items": items,
    }

    return response

class PaginatedResponse(BaseModel):
    total: int
    size: int
    page: int
    items: list
    next_page: Optional[str] = None
    previous_page: Optional[str] = None

    class Config:
        from_attributes = True


def does_referenced_record_exist(table_name: EntityNameEnum, record_id: int, db: Session):
        """
            Returns `true` if a referenced record in the `table_name` exists.
            Raises `ReferencedRecordNotFound` if record is not found.
        """
        referenced_table = table_name_to_model_map[table_name.value]
        existing_referenced_record = db.query(referenced_table).filter(referenced_table.id == record_id).first()

        if not existing_referenced_record:
            raise ReferencedRecordNotFound(
                f"""Referenced record does not exist. 
                    Confirm that a record with ID {record_id} exists in the `{table_name.value}` table.
                """
                )
        return True
