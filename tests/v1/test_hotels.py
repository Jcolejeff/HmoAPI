import pytest
import json
from decouple import config
from fastapi import status



def test_get_hotels(client, test_user, test_org):
    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    params = {"organization_id": test_org['id']}
    print(config('HNG_ORG_ID'))
    if not config("HNG_ORG_ID"):
        print('[HNG_ORG_ID] environment variable is not set. Skipping test')
        return 

    response = client.get(f"v1/hotels", headers=headers, params=params)

    assert response.status_code == status.HTTP_200_OK

    hotels = response.json()["items"]
    invalid_hotels = list(filter(lambda hotel: hotel["organization_id"] != config("HNG_ORG_ID"), hotels))

    assert len(hotels) > 1
    assert len(invalid_hotels) == 0



@pytest.mark.parametrize("location_type, location, status_code", [
    ('country', 'Nigeria', status.HTTP_200_OK),
    ('state', 'Akwa ibom', status.HTTP_200_OK),
    ('city', 'Kano', status.HTTP_200_OK),
    ('city', 'Ikeja', status.HTTP_200_OK),
    (None, 'Lagos', status.HTTP_400_BAD_REQUEST),
    ('state', None, status.HTTP_400_BAD_REQUEST),
])
def test_get_hotels_by_location(client, test_user, test_org, location_type, location, status_code):
    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    params = {"organization_id": test_org['id'],
              "location_type": location_type,
              "location": location}

    response = client.get(f"v1/hotels", headers=headers, params=params)

    assert response.status_code == status_code
