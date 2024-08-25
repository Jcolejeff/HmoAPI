from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import declarative_base

from main import app
from decouple import config
import json
from datetime import date

from api.db.database import get_db
from api.db.database import Base

from api.v1.organization.models import Role


DB_TYPE = config("DB_TYPE")
DB_NAME = config("DB_NAME")
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST")
DB_PORT = config("DB_PORT")
MYSQL_DRIVER = config("MYSQL_DRIVER")

SQLALCHEMY_DATABASE_URL_TEST = f'{DB_TYPE}+{MYSQL_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}_test'

engine = create_engine(SQLALCHEMY_DATABASE_URL_TEST)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def seed_roles(session):
    roles = [
        Role(name="Manager", permissions=[
            "read-request",
            "create-request",
            "update-request",
            "delete-request",
            "approve-request"
        ]),
        Role(name="Staff", permissions=[
            "read-request",
            "create-request",
            "update-request",
            "delete-request",
        ]),
        Role(name="Logistics", permissions=[
            "read-request",
            "create-request",
            "update-request",
            "delete-request",
            "approve-request"
        ])
    ]

    session.add_all(roles)
    session.commit()


@pytest.fixture
def test_user(client, seed_roles):
    payload = {
        "first_name": "meeena",
        "last_name": "reena",
        "email": "reena@gmail.com",
        "password": "password123",
        "unique_id": "1005"
    }
    res = client.post("/v1/auth/signup", data=json.dumps(payload))

    new_user = res.json()['data']
    new_user['access_token'] = res.json()['access_token']
    new_user['email'] = payload['email']
    return new_user


@pytest.fixture
def test_org(client, test_user, seed_roles):
    payload = {"name": "Test-Org"}

    headers = {'Authorization': 'Bearer {}'.format(test_user['access_token'])}

    res = client.post("v1/organizations",
                      data=json.dumps(payload), headers=headers)
    org = res.json()
    return org

@pytest.fixture
def test_request(client, test_user, test_org):
    payload = {
        "organization_id": test_org["id"],
        "country": "Nigeria",
        "state": "Lagos",
        "city": "VI",
        "start": "2024-08-08",
        "end": "2024-09-05",
        "purpose": "to chop life",
        "hotel": "Lagos Orient",
        "room": "string",
        "rate": 15000,
        "meal": "string",
        "transport": "string",
        "other_requests": "string",
        "requester_id": test_user['id'],
        "status": "pending"
    }

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    
    res = client.post('v1/requests', headers=headers, data=json.dumps(payload))

    return res.json()


@pytest.fixture
def test_group1(client, test_user, test_org):
    payload = {"name": "Test Group",
               "organization_id": test_org['id'],
               "description": "This is a test group for testing",
               "approval_levels": 2}

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    res = client.post("v1/groups",
                      data=json.dumps(payload), headers=headers)

    return res.json()


@pytest.fixture
def test_group2(client, test_user, test_org):
    payload = {"name": "Test Group 2",
               "organization_id": test_org['id'],
               "description": "This is a test group 2 for testing",
               "approval_levels": 2}

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    res = client.post("v1/groups",
                      data=json.dumps(payload), headers=headers)

    return res.json()


@pytest.fixture
def test_add_member1(client, test_user, test_org, test_group1):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    payload = {"organization_id": test_org['id'],
               "member_ids": [test_user["id"]]}

    res = client.post(f"v1/groups/{test_group1['id']}/members/add",
                      data=json.dumps(payload), headers=headers)
    
    return res.json()[0]


@pytest.fixture
def test_comment(client, test_user, test_org, test_group1):
    payload = {
        "content": "This is a test comment",
        "table_name": "groups",
        "record_id": test_group1['id'],
    }

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    response = client.post(
        "v1/comments", data=json.dumps(payload), headers=headers)

    return response.json()


@pytest.fixture
def test_comment2(client, test_user, test_org, test_group1):
    payload = {
        "content": "This is a test comment number 2",
        "table_name": "groups",
        "record_id": test_group1['id'],
    }

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    response = client.post(
        "v1/comments", data=json.dumps(payload), headers=headers)

    return response.json()
