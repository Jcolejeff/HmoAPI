from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.schema import sort_tables
from contextlib import contextmanager

from decouple import config
from api.db.database import Base

import datetime
from faker import Faker
import random
# import asyncio

from api.v1.user.services import UserService
from api.v1.auth.services import Auth as AuthService
from api.v1.user.schemas import CreateUser
from api.v1.organization.services import OrganizationService, OrganizationUserService
from api.v1.groups.services import GroupService
from api.v1.requests.services import RequestService
from api.v1.requests.schemas import CreateRequest
from api.v1.hotels.schemas import ApprovedHotelBase
from api.v1.hotels.services import HotelService
from api.v1.groups.schemas import CreateGroup

from api.v1.organization.schemas import CreateOrganization
from scripts.seed_roles import _seed_roles

fake = Faker()
user_service = UserService()
organization_service = OrganizationService()
request_service = RequestService()
hotel_service = HotelService()


DB_TYPE = config("DB_TYPE")
DB_NAME = config("DB_NAME")
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST")
DB_PORT = config("DB_PORT")
MYSQL_DRIVER = config("MYSQL_DRIVER")

DATABASE_URL = f'{DB_TYPE}+{MYSQL_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_sample_requests():
    requests = []
    for i in range(0, 5):
        req_start_dt = fake.date()
        splitted_start_dt = req_start_dt.split('-')
        # print(req_start_dt)
        req = {
            "state": fake.state(),
            "city": fake.city(),
            "country": fake.country(),
            "start": req_start_dt,
            "end": str(fake.date_between(
                start_date=datetime.date(int(splitted_start_dt[0]), int(splitted_start_dt[1]), int(splitted_start_dt[2])))),
            "purpose": fake.sentence(),
            "hotel": random.choice(sample_hotels),
            "room": "string",
            "meal": "Eba",
            "transport": "Korope",
            "other_requests": "Maybe life is a movie",
            "status": "pending"
        }

        requests.append(req)

    return requests

user_emails = ['admin@gmail.com', 'random@gmail.com', 'tester@gmail.com']
USER_PASSWORD = '1234567890'
group_names = ['HR', 'Finance', 'Engineering']
sample_hotels = ['Lagos Oriental', 'Four points', 'Sheraton',
                 'Eko hotel', 'Radisson Blue', 'Maison Fahrenheit']
approved_hotels = [
    {
        "hotel_name": 'Lagos Oriental',
        "state": "Lagos",
        "city": "Lekki",
        "country": "Nigeria"
    },
    {
        "hotel_name": 'Four points',
        "state": "Lagos",
        "city": "Victoria Island",
        "country": "Nigeria"
    },
    {
        "hotel_name": 'Sheraton',
        "state": "Lagos",
        "city": "Ikeja",
        "country": "Nigeria"
    },
    {
        "hotel_name": 'Sheraton',
        "state": "Abuja",
        "city": "CBD",
        "country": "Nigeria"
    },
    {
        "hotel_name": 'Presidential Hotel',
        "state": "Rivers",
        "city": "Portharcourt",
        "country": "Nigeria"
    },
    {
        "hotel_name": 'Protea Hotel',
        "state": "Edo",
        "city": "Benin",
        "country": "Nigeria"
    },
]

sample_requests = get_sample_requests()

def drop_db_tables():
    with SessionLocal() as db:
        db.execute(text('SET foreign_key_checks = 0'))

    Base.metadata.drop_all(bind=engine)

def create_db_tables():
    Base.metadata.create_all(bind=engine)

@contextmanager
def session():
    db = SessionLocal()
    try:
        yield db
    except:
        # if we fail somehow rollback the connection
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":

    drop_db_tables()
    create_db_tables()

    # create 3 users
    with session() as db:
        print("Creating users")
        users = []
        for email in user_emails:
            created_user = user_service.create(user=CreateUser(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=email,
                password=USER_PASSWORD
            ),
                db=db
            )

            print(created_user.__dict__, 'created user')
            users.append(created_user)

        print("Seeding roles")
        roles = _seed_roles(db=db)

        print("Creating organization")
        # create an organization with the first user
        organization = asyncio.run(organization_service.create(
            payload=CreateOrganization(
                name=fake.company(),
                slug=fake.slug(),
                created_by=users[0].id
            ),
            db=db)
        )

        organization_user_service = OrganizationUserService(
            organization_id=organization.id, db=db)

        print("Creating organization users")
        for user in users:
            # add the 3 users to the organization created
            org_user = organization_user_service.add_organization_user(
                user_id=user.id, role_id=roles[0].id if roles else 1)

        # create groups
        # add the users to the different groups
        print("Creating groups")
        for index, name in enumerate(group_names):
            asyncio.run(GroupService.create(
                payload=CreateGroup(
                    name=name,
                    organization_id=organization.id,
                    member_ids=[users[index].id],
                    approver_ids=[users[0].id]
                ),
                user_id=users[0].id,
                db=db
            ))

        print("Creating approved hotels")
        for hotel in approved_hotels:
            hotel["organization_id"] = organization.id

            asyncio.run(hotel_service.create(
                payload=ApprovedHotelBase(**hotel), db=db))

        print("Creating requests")
        for request in sample_requests:
            for user in users:
                request['organization_id'] = organization.id
                request['rate'] = fake.random_int(min=1000, max=10000)
                request['requester_id'] = user.id

                asyncio.run(request_service.create(
                    payload=CreateRequest(**request), db=db))

        print("Seeding completed")
        print("Test users: " +
              ', '.join([f"{user.email}" + '-1234567890' for user in users]))
