import requests
import pytest

CALENDAR_API = "http://127.0.0.1:5000"
KEYCLOAK_URL = "http://127.0.0.1:8080/"
KEYCLOAK_REALM = "calendar-realm"
KEYCLOAK_CLIENT = "calendar-client"

@pytest.fixture(scope="session")
def group_id(auth_headers):
    group_resp = requests.post(
        f"{CALENDAR_API}/groups/",
        json={
            "name": "Test Group python",
            "description": "pytest",
        },
        headers=auth_headers,
    )

    print(group_resp.json()['group']['id'])

    assert group_resp.status_code == 201
    return group_resp.json()["group"]["id"]

def test_get_group(auth_headers, group_id):
    groups_resp = requests.get(
        f"{CALENDAR_API}/groups/{group_id}",
        headers=auth_headers,
    )

    assert groups_resp.status_code == 200
    group_data = groups_resp.json()
    assert group_data["name"] == "Test Group python"
    assert group_data["description"] == "pytest"
    assert group_data["id"] == group_id

def test_add_member(auth_headers, group_id):
    member_resp = requests.post(
        f"{CALENDAR_API}/groups/{group_id}/users",
        json={"email": "bob@example.com"},
        headers=auth_headers,
    )

    assert member_resp.status_code == 201
    assert member_resp.json()["message"] == "User added to group"
    assert member_resp.json()["role"] == "member"

def test_set_organizer(auth_headers, group_id):
    organizer_resp = requests.put(
        f"{CALENDAR_API}/groups/{group_id}/users/organizer",
        json={"email": "bob@example.com"},
        headers=auth_headers,
    )

    assert organizer_resp.status_code == 200
    assert organizer_resp.json()["message"] == "User role changed successfully"
    assert organizer_resp.json()["role"] == "organizer"

def test_set_member(auth_headers, group_id):
    member_resp = requests.put(
        f"{CALENDAR_API}/groups/{group_id}/users/member",
        json={"email": "bob@example.com"},
        headers=auth_headers,
    )

    assert member_resp.status_code == 200
    assert member_resp.json()["message"] == "User role changed successfully"
    assert member_resp.json()["role"] == "member"

def test_get_group_members(auth_headers, group_id):
    members_resp = requests.get(
        f"{CALENDAR_API}/groups/{group_id}/users",
        headers=auth_headers,
    )

    assert members_resp.status_code == 200
    members_data = members_resp.json()
    assert "members" in members_data
    assert isinstance(members_data["members"], list)
    assert any(member["user_id"] == "69e481ac-57aa-4c1b-8417-8210e5808ba7" for member in members_data["members"])
    assert any(member["user_id"] == "a7f0c56c-4df4-406e-88d3-c8f634944eab" for member in members_data["members"])

# @pytest.mark.dependency(depends=["test_set_member"])
def test_invalid_permission_set_organizer(group_id):
    resp = requests.post(
        f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
        data={
            "client_id": KEYCLOAK_CLIENT,
            "grant_type": "password",
            "username": "bob",
            "password": "bob123",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert resp.status_code == 200, resp.text
    access_token = resp.json()["access_token"]
    auth_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.put(
        f"{CALENDAR_API}/groups/{group_id}/users/organizer",
        json={"email": "bob@example.com"},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"] == "User must have role 'organizer' for this action"

def test_remove_member(auth_headers, group_id):
    member_resp = requests.delete(
        f"{CALENDAR_API}/groups/{group_id}/users",
        json={"email": "bob@example.com"},
        headers=auth_headers,
    )

    assert member_resp.status_code == 200
    assert member_resp.json()["message"] == "User removed from group"

def test_remove_group(auth_headers, group_id):
    group_resp = requests.delete(
        f"{CALENDAR_API}/groups/{group_id}",
        headers=auth_headers,
    )

    assert group_resp.status_code == 200
    assert group_resp.json()["message"] == "Group deleted successfully"
