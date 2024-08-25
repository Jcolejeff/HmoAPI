import os
from typing import List

from api.core.base.services import Service
from api.v1.emails import schemas as email_schemas
from decouple import config
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from sqlalchemy.orm import Session

from .models import Email

conf = ConnectionConfig(
    MAIL_USERNAME=config('MAIL_USERNAME'),
    MAIL_PASSWORD=config('MAIL_PASSWORD'),
    MAIL_FROM=config('MAIL_FROM'),
    MAIL_PORT=config('MAIL_PORT'),
    MAIL_SERVER=config('MAIL_SERVER'),
    MAIL_FROM_NAME=config('MAIL_FROM_NAME'),
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=os.path.join(config('TEMPLATE_FOLDER')),
)


class EmailService:
    def __init__(self) -> None:
        pass

    @classmethod
    async def register(cls, payload: email_schemas.CreateEmail, data, db: Session, background_task: BackgroundTasks):
        email = Email(**payload.dict())
        db.add(email)
        db.commit()

        return email

    @classmethod
    async def send(cls, title: str, template_name: str, recipients: List[str], background_task: BackgroundTasks, template_data: dict, attachments: List[str] = None):

        message_schema = MessageSchema(
            subject=title,
            recipients=recipients,
            template_body=template_data,
            subtype="html",
            # attachments=[attachments if attachments else None]
        )

        fm = FastMail(conf)

        background_task.add_task(
            fm.send_message, message_schema, template_name=template_name)
