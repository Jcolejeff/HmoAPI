import json
from fastapi import status

def test_create_request_where_start_date_is_farther_than_end_date(client, test_user, test_org):
    payload = {
        "organization_id": test_org["id"],
        "country": "Nigeria",
        "state": "Lagos",
        "city": "VI",
        "start": "2024-09-05",
        "end": "2024-08-08",
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

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.json()['detail'] == "Start date cannot be farther than end date"

def test_create_request(client, test_user, test_org):
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

    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()['requester_id'] == test_user["id"]
    assert res.json()['organization_id'] == test_org["id"]
    assert res.json()['start'] == payload["start"]
    assert res.json()['end'] == payload["end"]


def test_update_request_without_status(client, test_request, test_user, test_org):
    payload = {
        "organization_id": test_org["id"],
        "country": "Nigeria",
        "state": "Lagos",
        "city": "VI",
        "start": "2024-10-08",
        "end": "2024-10-10",
        "purpose": "Testing update",
        "hotel": "Eko hotel",
        "room": "King size",
        "rate": 20000,
        "meal": "Rice",
        "transport": "Korope",
        "other_requests": "Bring my Martell",
    }

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    
    res = client.put(f'v1/requests/{test_request['id']}', headers=headers, data=json.dumps(payload))

    assert res.status_code == status.HTTP_200_OK
    assert res.json()['organization_id'] == test_org["id"]
    assert res.json()['start'] == payload["start"]
    assert res.json()['end'] == payload["end"]
    assert res.json()['city'] == payload["city"]
    assert res.json()['state'] == payload["state"]
    assert res.json()['room'] == payload["room"]
    assert res.json()['rate'] == payload["rate"]
    assert res.json()['meal'] == payload["meal"]
    assert res.json()['transport'] == payload["transport"]
    assert res.json()['other_requests'] == payload["other_requests"]
    

def test_update_request_with_approval_status(client, test_user, test_org):
    # Confirm the approver status from the request approver object
    # If the request approver is the only approver, confirm that the request status is set to approved
    pass

def test_update_request_with_highest_position_approver(client, test_request, test_user, test_org):
    pass

def test_update_request_with_lowest_position_approver(client, test_request, test_user, test_org):
    pass

def test_delete_request(client, test_user, test_org):
    pass

def test_get_requests(client, test_request, test_user, test_org):
    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    
    res = client.get('v1/requests', headers=headers, params={ "organization_id": test_org['id'] })

    assert res.status_code == status.HTTP_200_OK
    assert res.json()['total'] == 1 #only test_request was created
    assert len(res.json()['items']) == 1 #only test_request was created
    assert res.json()['items'][0]['id'] == test_request['id']

def test_get_request(client, test_request, test_user, test_org):
    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    
    res = client.get(f'v1/requests/{test_request['id']}', headers=headers, params={ "organization_id": test_org['id'] })

    assert res.status_code == status.HTTP_200_OK
    assert res.json()['organization_id'] == test_org["id"]
    assert res.json()['start'] == test_request["start"]
    assert res.json()['end'] == test_request["end"]
    assert res.json()['city'] == test_request["city"]
    assert res.json()['state'] == test_request["state"]
    assert res.json()['room'] == test_request["room"]
    assert res.json()['rate'] == test_request["rate"]
    assert res.json()['meal'] == test_request["meal"]
    assert res.json()['transport'] == test_request["transport"]
    assert res.json()['other_requests'] == test_request["other_requests"]