from fastapi import Depends, APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List
from sqlalchemy.orm import Session
from decouple import config
from api.v1.files import schemas as file_schemas
from api.v1.files.services import FileService
from api.db.database import get_db
from api.v1.user.schemas import ShowUser
from api.core.base.constants import EntityNameEnum
from api.core.dependencies.user import is_authenticated
from api.utils.utils import does_referenced_record_exist

app = APIRouter(tags=["Files"])

@app.post("/files/upload", status_code=status.HTTP_201_CREATED)
async def upload_file( 
    user: ShowUser = Depends(is_authenticated),
    files: List[UploadFile] = File(...),
    organization_id: str = Form(...),
    entity_name: EntityNameEnum = Form(...),
    entity_id: str = Form(...),
    db: Session = Depends(get_db)
):

    """
        Endpoint to upload a file to an entity in an organization

        Returns success message on success.

    """  
    payload = {
        "organization_id": organization_id,
        "entity_id": entity_id,
        "entity_name": entity_name
    }

    does_referenced_record_exist(table_name=entity_name, record_id=entity_id, db=db)

    payload = file_schemas.UploadFileSchema(**payload)
    
    await FileService.create(payload=payload, created_by=user.id, db=db, files=files)

    return "Files uploaded successfully"


@app.get("/files/{url:path}", status_code=status.HTTP_200_OK, response_class=FileResponse)
async def get_files(
    url: str,
    size: str = None,
    db: Session = Depends(get_db)
):

    """
        Endpoint to get file for an entity in an organization

        Returns file.

    """ 

    file = await FileService.get(url=url, size=size, db=db)

    return file




