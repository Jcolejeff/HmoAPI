from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from api.v1.user import schemas as user_schema
from api.db.database import get_db
from api.core.dependencies.user import is_authenticated, is_org_member
from api.v1.requests import schemas as req_schemas
from api.v1.requests.services import RequestService
from api.v1.emails.services import EmailService
from api.v1.user.services import UserService
from api.v1.auth.services import Auth
from api.v1.groups.services import GroupMemberService
from api.utils import paginator
from api.v1.requests.models import RequestStatusEnum
from datetime import timedelta
from api.utils.callingOpenaiForApprovedStatus import OpenAiService
from decouple import config

MAGIC_TOKEN_EXPIRE_MINUTES = int(config('ACCESS_TOKEN_EXPIRE_MINUTES'))

app = APIRouter(tags=["Requests"])


@app.post("/requests", status_code=status.HTTP_201_CREATED, response_model=req_schemas.ShowRequest)
async def create_request(
    payload: req_schemas.CreateRequest,
    background_task: BackgroundTasks,
    user: user_schema.ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db)
):
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)

    created_request = await RequestService.create(payload=payload, db=db)

    
    return created_request


@app.get("/requests", status_code=status.HTTP_200_OK, response_model=req_schemas.PaginatedRequestsResponse)
async def get_requests(
    organization_id: int,
    status: req_schemas.RequestStatusEnum = None,
    requester: int = None,
    approver: int = None,
    user: user_schema.ShowUser = Depends(is_org_member),
    db: Session = Depends(get_db),
    size: int = 20,
    page: int = 1,
):
    page_size = 20 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    requests, total = await RequestService.fetch_all(
        org_id=organization_id,
        db=db,
        size=page_size,
        offset=offset,
        requester=requester,
        approver=approver,
        status=status
    )

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint='/requests',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map((lambda request: req_schemas.ShowRequest.model_validate(request)), requests)))

    return response


@app.get("/requests/{id}", status_code=status.HTTP_200_OK, response_model=req_schemas.ShowRequest)
async def get_request(
    id: int,
    organization_id: int,
    user: user_schema.ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db)
):
    await is_org_member(organization_id=organization_id, user=user, db=db)

    request = await RequestService.get_request_in_organization(id=id, org_id=organization_id, db=db)

    return request


@app.put("/requests/{id}", status_code=status.HTTP_200_OK, response_model=req_schemas.ShowRequest)
async def update_request(
    id: int,
    payload: req_schemas.UpdateRequest,
    background_task: BackgroundTasks,
    user: user_schema.ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db)
):
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)

    update_request = await RequestService.update_request_in_organization(id=id, payload=payload, updater=user.id, db=db)
    
    if update_request.status == RequestStatusEnum.APPROVED.value:
        print("Request approved", update_request.id, update_request.status) 
        print("Calling OpenAI with the request id", update_request.id, update_request.status)  
        
        # Initialize the OpenAiService with the db session
        openai_service = OpenAiService(api_key='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', db=db)
        
        # Call OpenAI service asynchronously
        background_task.add_task(openai_service.call_openai, payload=update_request, request_id=update_request.id, author_id=user.id)

    return update_request