from fastapi import Depends
from api.db.database import SessionLocal
from api.v1.organization.models import Role
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_

manager_permissions = [
    "read-request",
    "create-request",
    "update-request",
    "delete-request",
    "approve-request"
]

staff_permissions = [
    "read-request",
    "create-request",
    "update-request",
    "delete-request",
]

logistics_permissions = [
    "read-request",
    "create-request",
    "update-request",
    "delete-request",
    "approve-request"
]


def _seed_roles(db: Session):
    """
        Needs a DB session
    """
    roles = db.query(Role).filter(or_(Role.name == "Manager",
                                        Role.name == "Staff", Role.name == "Logistics")).first()
    if roles:
        pass
    else:
        manager = Role(
            name="Manager",
            permissions=manager_permissions,
        )

        staff = Role(
            name="Staff",
            permissions=staff_permissions,
        )

        logistics = Role(
            name="Logistics",
            permissions=logistics_permissions,
        )

        db.add(manager)
        db.add(staff)
        db.add(logistics)
        db.commit()

        return [manager, staff, logistics]

        

def seed_roles():
    with SessionLocal() as db:
        _seed_roles(db=db)