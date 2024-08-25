import pytest
from fastapi import status
import json
from datetime import date


def test_create_comment(client, test_user, test_org, test_group1):
    payload = {
        "content": "This is a test comment",
        "table_name": "groups",
        "record_id": test_group1['id'],
    }

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    response = client.post(
        "v1/comments", data=json.dumps(payload), headers=headers)

    assert response.status_code == 201
    assert response.json()["content"] == payload['content']


def test_get_comment(client, test_user, test_comment, test_org):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    response = client.get(f"v1/comments/{test_comment['id']}", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["content"] == test_comment['content']


def test_get_comments(client, test_user, test_group1, test_comment, test_comment2, test_org):

    params = {"table_name": "groups",
              "record_id": test_group1['id']}

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    response = client.get("/v1/comments", headers=headers, params=params)

    assert response.status_code == status.HTTP_200_OK

    assert response.json()['total'] >= 1


def test_update_comment(client, test_user, test_group1, test_comment, test_org):

    payload = {
        "content": "Update test comment",
        "table_name": "groups",
        "record_id": test_group1["id"],
        "author": test_user['id']
    }

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}
    response = client.put(f"/v1/comments/{test_comment['id']}",
                          data=json.dumps(payload),
                          headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["content"] == payload['content']


def test_delete_comment(client, test_user, test_group1, test_comment, test_org):

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    response = client.delete(
        f"/v1/comments/{test_comment['id']}", headers=headers)

    assert response.status_code == 204


def test_get_comments_by_parent(client, test_user, test_group1, test_comment, test_org):

    child_comment_payload = {
        "content": "This is a child comment",
        "table_name": "groups",
        "record_id": test_group1['id'],
        "parent_id": test_comment['id'],
    }

    headers = {'Authorization': f'Bearer {test_user["access_token"]}'}

    response = client.post(
        "/v1/comments/", data=json.dumps(child_comment_payload), headers=headers)

    assert response.status_code == status.HTTP_201_CREATED

    params = {"record_id": test_comment['record_id'],
              "table_name": test_comment['table_name'],
              "parent_id": test_comment['id']}

    response = client.get(f"/v1/comments", headers=headers, params=params)

    assert response.status_code == status.HTTP_200_OK
