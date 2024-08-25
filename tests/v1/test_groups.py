import json
from fastapi import status


def test_create_group(client, test_user, test_org):
    payload = {"name": "Test Group",
               "organization_id": test_org['id'],
               "description": "This is a test group for testing",
               "approval_levels": 2}

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    res = client.post("v1/groups/",
                      data=json.dumps(payload), headers=headers)

    assert res.status_code == 201
    assert res.json()["name"] == "Test Group"
    assert res.json()["approval_levels"] == 2


def test_get_groups(client, test_user, test_org, test_group1, test_group2):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    params = {"organization_id": test_org['id']}

    res = client.get("v1/groups/",
                     params=params, headers=headers)

    assert len(res.json()["items"]) == 2
    assert res.status_code == 200


def test_add_members(client, test_user, test_org, test_group1):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    payload = {"organization_id": test_org['id'], "member_ids": [test_user["id"]]}

    res = client.post(f"v1/groups/{test_group1['id']}/members/add",
                      data=json.dumps(payload), headers=headers)
    
    response_data: dict = res.json()[0]

    assert res.status_code == 201
    assert response_data['member_id'] == test_user['id']

    # Ensure that the member and group fields are returned
    assert 'member' in response_data.keys()
    assert 'group' in response_data.keys()



def test_remove_members(client, test_user, test_org, test_group1, test_add_member1):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    payload = {"organization_id": test_org['id'],
               "member_ids": [test_add_member1['member_id']]}

    res = client.post(f"v1/groups/{test_group1['id']}/members/remove",
                      data=json.dumps(payload), headers=headers)
    
    assert res.status_code == 200
    assert res.json() == f"User(s) with IDs [{test_add_member1['member_id']}] removed successfully"


def test_get_members(client, test_user, test_org, test_group1, test_add_member1):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    params = {"organization_id": test_org['id']}

    res = client.get(f"v1/groups/{test_group1['id']}/members",
                     params=params, headers=headers)

    print(res.json())

    assert res.status_code == 200
    assert res.json()['total'] == 1 #only create test_add_member1 in this text
    assert len(res.json()['items']) == 1 #only create test_add_member1 in this text


