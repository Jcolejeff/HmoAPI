from api.core.base.services import Service
from api.v1.groups import schemas as g_schemas
from sqlalchemy.orm import Session
from sqlalchemy import exc as SQLALchemyExceptions
from sqlalchemy.sql import and_
from sqlalchemy import delete

from api.v1.groups.models import Group, GroupMember, GroupApprover
from api.v1.groups.exceptions import (
    GroupNotFoundException, MemberNotFoundException,
    DuplicateGroupNameException, ApproverNotFoundException
)


class GroupService(Service):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    async def create(cls, payload: g_schemas.CreateGroup, user_id: int, db: Session) -> g_schemas.ShowGroup:
        group_with_same_name = db.query(Group).filter(and_(
            Group.name == payload.name, Group.is_deleted == False, Group.organization_id == payload.organization_id)).first()

        if group_with_same_name:
            raise DuplicateGroupNameException()

        created_group = Group(
            organization_id=payload.organization_id,
            name=payload.name,
            description=payload.description,
            parent_group_id=payload.parent_group_id,
            approval_levels=payload.approval_levels,
            created_by=user_id
        )

        db.add(created_group)
        db.commit()

        if payload.approver_ids:
            group_approver_service = GroupApproverService(
                group_id=created_group.id,
                organization_id=created_group.organization_id,
                db=db
            )

            await group_approver_service.add_group_approvers(approver_ids=payload.approver_ids)

        if payload.member_ids:
            group_member_service = GroupMemberService(
                group_id=created_group.id,
                organization_id=created_group.organization_id,
                db=db
            )

            await group_member_service.add_group_members(member_ids=payload.member_ids)

        db.refresh(created_group)

        return created_group

    @classmethod
    def get(cls):
        pass

    @classmethod
    def update(cls):
        pass

    @classmethod
    def delete(cls):
        pass

    @classmethod
    def get_organization_group(cls, id: int, organization_id: int, db: Session) -> g_schemas.ShowGroup:
        group = db.query(Group).filter(and_(
            Group.id == id, Group.organization_id == organization_id, Group.is_deleted == False)).first()

        if not group:
            raise GroupNotFoundException()

        return group

    @classmethod
    async def delete_organization_group(cls, id: int, organization_id: int, db: Session) -> g_schemas.ShowGroup:
        """
            Soft-deletes a group in an organization
        """
        group = cls.get_organization_group(
            id=id, organization_id=organization_id, db=db)

        group.is_deleted = True

        db.commit()
        db.refresh(group)

        return group

    @classmethod
    async def update_organization_group(cls, id: int, payload: g_schemas.UpdateGroup, db: Session) -> g_schemas.ShowGroup:
        """
            Updates a group in an organization
        """
        group = cls.get_organization_group(
            id=id, organization_id=payload.organization_id, db=db)

        if payload.name:
            group.name = payload.name

        if payload.description:
            group.description = payload.description

        if payload.approval_levels:
            group.approval_levels = payload.approval_levels

        if payload.parent_group_id:
            group.parent_group_id = payload.parent_group_id

        db.commit()
        db.refresh(group)

        return group

    @classmethod
    async def fetch_all(cls, org_id: int, db: Session, size: int = 50, offset: int = 50) -> tuple:
        base_query = db.query(Group).filter(
            and_(Group.organization_id == org_id, Group.is_deleted == False))

        total = base_query.count()
        requests = base_query.limit(limit=size).offset(offset=offset).all()

        return requests, total


class GroupMemberService:
    def __init__(self, group_id: int, organization_id: int, db: Session) -> None:
        """
            A group can only exist within the context of an organization, 
            so it makes sense to require an `organization_id` when initialization a `GroupMemberService` object.
            The `__init__` method also checks if the group exists in the organization.
        """
        self.group_id = group_id
        self.organization_id = organization_id
        self.db = db

        existing_group = GroupService.get_organization_group(
            id=self.group_id, organization_id=self.organization_id, db=db)
        self.group = existing_group

    async def add_group_members(self, member_ids: list[int]) -> list[g_schemas.ShowGroupMember]:
        """
            Adds a user to a group. If the user already exists as a member, it fails gracefully.
        """
        # CHECK THAT GROUP AND MEMBERS TO BE ADDED ARE IN THE SAME ORGANIZATION
        added_members = []
        for member_id in member_ids:
            added_member = GroupMember(
                group_id=self.group_id,
                member_id=member_id
            )

            self.db.add(added_member)
            try:
                self.db.commit()
            except SQLALchemyExceptions.IntegrityError as ex:
                # this would handle fail FK checks incase the member_id passed doesn't exist as a user id in the self.DB
                # and if a member with the group_id and member_id already exists in the self.DB.
                self.db.rollback()
                continue

            self.db.refresh(added_member)

            added_members.append(added_member)

        return added_members

    async def remove_group_members(self, member_ids: list[int]) -> str:
        member_count = self.db.query(GroupMember).filter(and_(GroupMember.member_id.in_(
            member_ids), GroupMember.group_id == self.group_id)).count()

        if member_count != len(member_ids):
            raise MemberNotFoundException()

        query = delete(GroupMember).where(
            GroupMember.member_id.in_(member_ids))
        self.db.execute(query)

        self.db.commit()

        return f"User(s) with IDs {member_ids} removed successfully"

    async def get_group_members(self, size: int = 50, offset: int = 0):
        query = self.db.query(GroupMember).filter(
            GroupMember.group_id == self.group_id)

        count = query.count()
        members = query.offset(offset=offset).limit(limit=size).all()

        return members, count

    @staticmethod
    def get_user_group(user_id: int, db: Session):
        group = db.query(Group).join(GroupMember, Group.id == GroupMember.group_id).filter(
            GroupMember.member_id == user_id).first()
        return group

    @staticmethod
    def get_user_approvers(user_id: int, db: Session):
        approvers = db.query(GroupApprover).join(GroupMember, GroupApprover.group_id == GroupMember.group_id).filter(
            GroupMember.member_id == user_id).all()

        return approvers


class GroupApproverService:
    def __init__(self, group_id: int, organization_id: int, db: Session) -> None:
        """
            A group can only exist within the context of an organization, 
            so it makes sense to require an `organization_id` when initialization a `GroupApproverService` object.
            The `__init__` method also checks if the group exists in the organization.
        """
        self.group_id = group_id
        self.organization_id = organization_id
        self.db = db

        existing_group = GroupService.get_organization_group(
            id=self.group_id, organization_id=self.organization_id, db=db)
        self.group = existing_group

    async def add_group_approvers(self, approver_ids: list[int]):
        # CHECK THAT GROUP AND APPROVERS TO BE ADDED ARE IN THE SAME ORGANIZATION
        added_approvers: list[GroupApprover] = []
        for approver_id in approver_ids:
            group_approver = GroupApprover(
                group_id=self.group_id,
                approver_id=approver_id
            )

            self.db.add(group_approver)

            try:
                self.db.commit()
            except SQLALchemyExceptions.IntegrityError as ex:
                # this would handle fail FK checks incase the approver_id passed doesn't exist as a user id in the DB
                # and if an approver with the group_id and approver_id already exists in the DB.
                self.db.rollback()
                continue

            self.db.refresh(group_approver)
            added_approvers.append(group_approver)

        return added_approvers

    async def remove_group_approvers(self, approver_ids: list[int]):
        member_count = self.db.query(GroupApprover).filter(and_(GroupApprover.approver_id.in_(
            approver_ids), GroupApprover.group_id == self.group_id)).count()

        if member_count != len(approver_ids):
            raise ApproverNotFoundException()

        query = delete(GroupApprover).where(
            GroupApprover.approver_id.in_(approver_ids))
        self.db.execute(query)

        self.db.commit()

        return f"User(s) with IDs {approver_ids} removed successfully"

    async def get_group_approvers(self, size: int = 50, offset: int = 0):

        query = self.db.query(GroupApprover).filter(
            GroupApprover.group_id == self.group_id)

        count = query.count()
        approvers = query.offset(offset=offset).limit(limit=size).all()

        return approvers, count
