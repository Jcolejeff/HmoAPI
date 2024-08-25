from pydantic import BaseModel
from typing import Optional

from api.core.base.constants import EntityNameEnum

class FileBase(BaseModel):
    organization_id: int 
    file_name: str
    file_path: Optional[str] = None
    entity_name: Optional[str] = None
    entity_id: int
    description: Optional[str] = None
    order : Optional[int] = None
    created_by: int

    class Config:
        from_attributes = True


class UploadFileSchema(BaseModel):
    organization_id: int 
    entity_name: EntityNameEnum
    entity_id: int


class ShowFile(BaseModel):
    id: int 
    url: str
    description: Optional[str] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True