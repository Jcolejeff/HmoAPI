from pydantic import BaseModel, validator
from typing import Optional, List, Any
from .models import EmailStatus


class SignInMail(BaseModel):
    title: str
    subject: str
    recipient_name: str
    body_message: str


class EmailBase(BaseModel):
    id: Optional[int] = None
    recipients: List[str]
    organization_id: int
    title: str
    body: str
    status: EmailStatus = EmailStatus.PENDING.value
    priority: Optional[int] = None
    template_name: str
    data: Any

    class Config:
        from_attributes = True

    @validator('data')
    def valid_data(cls, data, values):
        template_name = values.get('template_name')
        if template_name == "hello.html":
            if type(data) != SignInMail:
                raise ValueError('Invalid data for chosen Template')
        return data


class CreateEmail(EmailBase):
    pass
