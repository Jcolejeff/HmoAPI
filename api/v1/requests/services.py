from datetime import datetime
from sqlalchemy import exc as SQLALchemyExceptions

from api.core.base.services import Service
from api.v1.requests import schemas as req_schemas
from api.v1.requests.models import Request as RequestModel, RequestStatusEnum, RequestApproval
from api.v1.groups.models import GroupMember, GroupApprover
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_
from api.v1.requests.exceptions import (
    RequestNotFoundException,
    NotAllowedToUpdateRequestStatusException,
    LowerApproverHasNotApprovedException
)


class RequestService(Service):
    def __init__(self) -> None:
        super().__init__()
    
    def fetch(self):
        pass

    @classmethod
    async def create(cls, payload: req_schemas.CreateRequest, db: Session) -> req_schemas.ShowRequest:
        """
            Create a request
        """
        created_request = RequestModel(
            organization_id=payload.organization_id,
            state=payload.state,
            city=payload.city,
            country=payload.country,
            start=payload.start,
            end=payload.end,
            purpose=payload.purpose,
            hotel=payload.hotel,
            room=payload.room,
            rate=payload.rate,
            meal=payload.meal,
            transport=payload.transport,
            other_requests=payload.other_requests,
            requester_id=payload.requester_id,
            rejection_reason=payload.rejection_reason,
            status=payload.status.value  
        )

        db.add(created_request)
        db.commit()

        required_group_approvers = (
                db.query(GroupApprover)
                .join(GroupMember, GroupMember.member_id == created_request.requester_id)
                .filter(GroupApprover.group_id == GroupMember.group_id)
                .all()
        )

        for group_approver in required_group_approvers:
            # create request approval entries
                request_approval = RequestApproval(
                    request_id=created_request.id,
                    approver_id=group_approver.approver_id,
                    position=group_approver.position,
                    status=RequestStatusEnum.PENDING.value,
                    )
                
                db.add(request_approval)

                try:
                    db.commit()
                except SQLALchemyExceptions.IntegrityError as ex:
                # this would handle fail FK checks incase the approver_id passed doesn't exist as a user id in the DB
                # and if an approval with the request_id and approver_id already exists in the DB.
                    db.rollback()
                    continue

        return created_request

    @classmethod
    async def update(cls):
        pass

    @classmethod
    def delete(cls):
        pass

    @classmethod
    async def get_request_in_organization(cls, id: int, org_id: int, db: Session) -> req_schemas.ShowRequest:
        """
            Get request in an organization by ID
        """
        request = db.query(RequestModel).filter(and_(
            RequestModel.id == id, RequestModel.organization_id == org_id, RequestModel.is_deleted == False)).first()

        if not request:
            raise RequestNotFoundException()

        return request

    @classmethod
    async def get(cls, id: int, db: Session):
        """
            Get a request by ID
        """
        request = db.query(RequestModel).filter(
            and_(RequestModel.id == id, RequestModel.is_deleted == False)).first()

        if not request:
            raise RequestNotFoundException()

        return request

    @classmethod
    async def fetch_all(
        cls,
        org_id: int,
        db: Session,
        requester: int = None,
        status: RequestStatusEnum = None,
        approver: int = None,
        size: int = 50,
        offset: int = 0
    ) -> tuple:
        """
            Returns the requests objects matching the filters and the total number of requests for the organization with `org_id` as (requests, total)
        """

        base_query = db.query(RequestModel).filter(
            and_(RequestModel.organization_id == org_id, RequestModel.is_deleted == False))

        if approver:
            # not working correctly, pulling requests for other approvers
            base_query = (
                base_query.join(
                    GroupMember, GroupMember.member_id == RequestModel.requester_id)
                .join(GroupApprover, GroupApprover.group_id == GroupMember.group_id)
                .filter(GroupApprover.approver_id == approver)
            )

        if requester:
            base_query = base_query.filter(RequestModel.requester_id == requester)

        if status:
            base_query = base_query.filter(RequestModel.status == status.value)

        print(base_query)

        total = base_query.count()
        requests = base_query.order_by(RequestModel.date_created.desc()).limit(
            limit=size).offset(offset=offset).all()

        return requests, total

    @classmethod
    async def update_request_in_organization(cls, id: int, payload: req_schemas.UpdateRequest, updater: int, db: Session):
        """
            Update a request in an organization.
        """
        request = await cls.get_request_in_organization(id=id, org_id=payload.organization_id, db=db)
        request_approval_service = RequestApprovalService(request_id=id)
        request_approvals = request_approval_service.fetch_all(
            approver_id=updater, db=db)

        if payload.status:
            updater_request_approval = [
                approval for approval in request_approvals if approval.approver_id == updater]
            
            if len(updater_request_approval) == 0:
                raise NotAllowedToUpdateRequestStatusException()

            updater_request_approval = updater_request_approval[0]

            """
                If the lo position hasn't set approval status, the hi position shouldn't be able to
            """
            lower_approval = None

            for approval in request_approvals:
                is_lower_approver = approval.position == updater_request_approval.position - 1
                if is_lower_approver:
                    lower_approval = approval

            """
                Lowest approver must approve before any higher approver on the hierarchy
            """
            if lower_approval:
                lower_approver_has_not_approved = lower_approval.status == RequestStatusEnum.PENDING.value

                if lower_approver_has_not_approved:
                    raise LowerApproverHasNotApprovedException()

            """
                If updater has the highest position in `updated_request_approvals`, 
                set request status to approver status.
            """

            # update request approval
            request_approval_service.update(
                id=updater_request_approval.id,
                payload=req_schemas.UpdateRequestApproval(
                    **{"status": payload.status}),
                db=db
            )

            # Using the DB as the single source of truth here instead of updating the `request_approvals` in memory
            updated_request_approvals = request_approval_service.fetch_all(
                approver_id=updater, db=db)

            """
                Has the highest guy approved?
            """
            max_position = max(
                [updated_request_approval.position for updated_request_approval in updated_request_approvals])
            highest_position_approver = (
                db.query(RequestApproval)
                .filter(
                    RequestApproval.request_id == request.id, RequestApproval.position == max_position
                ).first()
            )

            if highest_position_approver:
                request.status = highest_position_approver.status

        if payload.state:
            request.state = payload.state

        if payload.city:
            request.city = payload.city

        if payload.hotel:
            request.hotel = payload.hotel

        if payload.meal:
            request.meal = payload.meal
        
        if payload.rate:
            request.rate = payload.rate
        
        if payload.room:
            request.room = payload.room

        if payload.purpose:
            request.purpose = payload.purpose

        if payload.start:
            request.start = payload.start

        if payload.end:
            request.end = payload.end
        
        if payload.transport:
            request.transport = payload.transport

        if payload.other_requests:
            request.other_requests = payload.other_requests
        
        request.last_updated = datetime.now()

        db.commit()
        db.refresh(request)

        return request


class RequestApprovalService(Service):
    def __init__(self, request_id: int) -> None:
        super().__init__()
        self.request_id = request_id

    def fetch(self, id: int, db: Session):
        return db.query(RequestApproval).filter(RequestApproval.id == id).first()

    def get_by_approver_id(self, approver_id: int, db: Session):
        return (
            db.query(RequestApproval)
            .filter(RequestApproval.request_id == self.request_id, RequestApproval.approver_id == approver_id)
            .first()
        )

    def fetch_all(self, approver_id: int, db: Session):
        return (
            db.query(RequestApproval)
            .filter(RequestApproval.request_id == self.request_id, RequestApproval.approver_id == approver_id)
            .all()
        )

    def update(self, id: int, payload: req_schemas.UpdateRequestApproval, db: Session):
        request_approval = self.fetch(id=id, db=db)

        request_approval.status = payload.status.value
        request_approval.last_updated = datetime.now()

        db.commit()

        return request_approval

    def create(self):
        return super().create()

    def delete(self):
        pass

    def delete(self):
        pass

    def get_dominant_approval_status(self, statuses: list[RequestStatusEnum]):
        status_map: dict[RequestStatusEnum, int] = {
            RequestStatusEnum.APPROVED.value: 0,
            RequestStatusEnum.PENDING.value: 0,
            RequestStatusEnum.REJECTED.value: 0,
        }

        # confirm that approvals status are the same before setting status. else it should be pending
        for status in statuses:
            status_map[status] += 1

        dominant_status: RequestStatusEnum = RequestStatusEnum.PENDING.value

        for status in [RequestStatusEnum.APPROVED.value, RequestStatusEnum.PENDING.value, RequestStatusEnum.REJECTED.value]:
            if status_map[status] > status_map[dominant_status]:
                dominant_status = status

        return dominant_status
