import json
from fastapi import status


def test_create_org(client, test_user):
    payload = {"name": "Test Org"}

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    res = client.post("v1/organizations/",
                      data=json.dumps(payload), headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["name"] == "Test Org"
    assert res.status_code == 201


def test_get_orgs(client, test_user, test_org):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    res = client.get("v1/organizations/", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["items"]) == 1
    assert res.json()["items"][0]["name"] == test_org['name']
    assert res.status_code == 200


def test_get_org(client, test_user, test_org):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    response = client.get(
        f"v1/organizations/{test_org['id']}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == test_org['name']


def test_get_org_users(client, test_user, test_org):
    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    response = client.get(
        f"v1/organizations/{test_org['id']}/users", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
