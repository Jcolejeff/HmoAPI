from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_
from decouple import config
from pydantic import EmailStr
from typing import Optional

from sqlalchemy import exc as SQLALchemyExceptions

from api.v1.organization.models import Organization, OrganizationUser, OrganizationInvite, RoleEnum, Role
from api.v1.organization import schemas as organization_schemas
from api.v1.user.schemas import ShowUser
from api.v1.organization.exceptions import OrganizationNotFoundException, InviteNotFoundException
from api.v1.user.services import UserService
from api.core.base.services import Service
from api.v1.emails.services import EmailService
from slugify import slugify
import random
import datetime


SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config("ALGORITHM")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
JWT_REFRESH_EXPIRY = int(config("JWT_REFRESH_EXPIRY"))
DEFAULT_ORG_ROLES = ["Admin", "Regular"]


class OrganizationService(Service):

    def __init__(self) -> None:
        pass

    @classmethod
    async def create(cls, payload: organization_schemas.CreateOrganization, db: Session):
        org_slug = slugify(payload.name)

        existing_org_with_slug = await cls.get_by_slug(db=db, slug=org_slug)

        created_org = Organization(
            name=payload.name.strip(),
            image_url=payload.image_url.strip() if payload.image_url else None,
            slug=org_slug if not existing_org_with_slug else f"{org_slug}-{random.randint(1, len(payload.name))}",
            created_by=payload.created_by  # should be set before using this service
        )
        db.add(created_org)
        db.commit()

        await cls.add_user_to_org(user_id=payload.created_by, organization_id=created_org.id, role=RoleEnum.MANAGER.value, db=db)
        db.refresh(created_org)

        return created_org

    @staticmethod
    async def get(db: Session, id: int) -> organization_schemas.ViewOrganization:
        org = db.query(Organization).filter(Organization.id == id).first()

        return org

    @staticmethod
    async def get_by_slug(db: Session, slug: str) -> organization_schemas.ViewOrganization:
        org = db.query(Organization).filter(
            Organization.slug == slug.strip()).first()

        return org

    @staticmethod
    async def get_or_throw(db: Session, id: int = None) -> organization_schemas.ViewOrganization:
        org = db.query(Organization).filter(Organization.id == id).first()

        if not org:
            raise OrganizationNotFoundException()

        return org

    @staticmethod
    async def fetch_all(user_id: str, db: Session):
        query = db.query(Organization).join(OrganizationUser, OrganizationUser.organization_id ==
                                            Organization.id).filter(OrganizationUser.user_id == user_id)

        total = query.all()
        count = query.count()  # change to the more efficient count method

        return (total, count)

    async def update(self):
        pass

    async def fetch(self):
        pass

    @classmethod
    async def delete(cls, db: Session, id: int = None, unique_id: str = None):

        return None

    @classmethod
    async def add_user_to_org(cls, user_id: str, organization_id: str, db: Session, role: RoleEnum = RoleEnum.STAFF.value):
        fetched_role = db.query(Role).filter(
            Role.name == role, Role.is_deleted == False).first()
        org_user = OrganizationUser(
            user_id=user_id,
            organization_id=organization_id,
            role_id=fetched_role.id
        )

        db.add(org_user)
        db.commit()
        db.refresh(org_user)

        return org_user

    @staticmethod
    async def get_organization_user(user_id: str, organization_id: str, db: Session):
        user = (db.query(OrganizationUser).filter(and_(OrganizationUser.user_id == user_id,
                                                       OrganizationUser.is_deleted == False,
                                                       OrganizationUser.organization_id == organization_id))
                .first())
        return user

    async def get_organization_users(organization_id: str, db: Session):
        users = (db.query(OrganizationUser).filter(and_(
            OrganizationUser.is_deleted == False,
            OrganizationUser.organization_id == organization_id))
            .all())
        return users

    @classmethod
    async def create_organization_invite(cls, email: EmailStr, organization_id: int, inviter_id: int, db: Session, existing_user: Optional[ShowUser] = None):
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        print(expires_at)

        # check if invite exist
        existing_invite = db.query(OrganizationInvite).filter(
            OrganizationInvite.reciever_email == email, OrganizationInvite.organization_id == organization_id).first()

        if not existing_invite:
            # create invite
            invite = OrganizationInvite(
                reciever_id=existing_user.id if existing_user else None,
                inviter_id=inviter_id,
                organization_id=organization_id,
                reciever_email=email,
                status="PENDING",
                expires_at=expires_at
            )

            db.add(invite)
            db.commit()
        else:
            existing_invite.status = "PENDING"
            existing_invite.expires_at = expires_at

            invite = existing_invite

        return invite

    @classmethod
    async def get_organization_invite_by_token(cls, invite_token: str, db: Session):
        existing_invite = db.query(OrganizationInvite).filter(
            OrganizationInvite.token == invite_token).first()

        if not existing_invite:
            raise InviteNotFoundException()

        return existing_invite

    @classmethod
    async def get_user_invites(cls, email: str, db: Session):
        query = db.query(OrganizationInvite).filter(OrganizationInvite.reciever_email ==
                                                    email, OrganizationInvite.status == organization_schemas.InviteStatusEnum.PENDING)

        count = query.count()
        result = query.all()

        return result, count

    @classmethod
    async def update_invite(cls, invite_token: str, user_id: int, status: organization_schemas.InviteStatusEnum, db: Session):
        existing_invite = await cls.get_organization_invite_by_token(invite_token=invite_token, db=db)

        existing_invite.status = status
        db.commit()

        # create org user ref
        if (status == organization_schemas.InviteStatusEnum.ACCEPTED):

            # get staff role id (extend this later to allow users send the role theyre inviting as)
            role = db.query(Role).filter(
                Role.name == "Staff").first()

            # create organization user
            organization_user = OrganizationUser(
                user_id=user_id,
                organization_id=existing_invite.organization_id,
                role_id=role.id,
            )
            db.add(organization_user)
            db.commit()

        return existing_invite

    @classmethod
    async def send_invites(cls, emails: list[EmailStr], organization: organization_schemas.ViewOrganization, user: ShowUser, db: Session, background_task):
        invite_response = {}
        for email in emails:
            existing_user = UserService.fetch_by_email(email=email, db=db)

            if (existing_user):
                existing_user_in_org = await cls.get_organization_user(user_id=existing_user.id, organization_id=organization.id, db=db)

                if (existing_user_in_org):
                    invite_response[email] = True

            # create organization invite
            invite = await cls.create_organization_invite(email=email, organization_id=organization.id, db=db, existing_user=existing_user, inviter_id=user.id)

            if existing_user:
                invite_link = f'{config("APP_URL")}/auth/signin?invite_token={invite.token}'
            else:
                invite_link = f'{config("APP_URL")}/auth/signup?invite_token={invite.token}&email={email}'

            # await send invite email
            try:
                data = {
                    "organization_name": organization.name,
                    "invite_link": invite_link
                }
                await EmailService.send(
                    title=f"Action required: {organization.name} invited you to join their organization on TravelApp.",
                    template_name="invite.html",
                    recipients=[email],
                    background_task=background_task,
                    template_data=data
                )

                invite_response[email] = True

            except Exception as ex:
                print(ex)
                invite_response[email] = False

        return invite_response

    @classmethod
    async def get_organization_invites(cls, organization_id: int, db: Session,  search_value: Optional[str] = None, offset: int = 1, limit: int = 20):
        query = db.query(OrganizationInvite).filter(
            OrganizationInvite.organization_id == organization_id)

        if search_value:
            query = query.filter(OrganizationInvite.reciever_email.ilike(
                f"%{search_value.lower()}%"))

        count = query.count()
        result = query.order_by(OrganizationInvite.created_at.desc()).offset(
            offset).limit(limit).all()

        return result, count


class OrganizationUserService:
    def __init__(self, organization_id: int, db: Session) -> None:
        self.organization_id = organization_id
        self.db = db

    def add_organization_user(self, user_id: int, role_id: int):
        organization_user = OrganizationUser(
            organization_id=self.organization_id,
            user_id=user_id,
            role_id=role_id
        )

        self.db.add(organization_user)

        try:
            self.db.commit()
        except SQLALchemyExceptions.IntegrityError as ex:
            # this would handle fail FK checks incase the member_id passed doesn't exist as a user id in the self.DB
            # and if a member with the group_id and member_id already exists in the self.DB.
            self.db.rollback()

        return organization_user
