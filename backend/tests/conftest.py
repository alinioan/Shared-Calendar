import pytest
import requests
import time

KEYCLOAK_URL = "http://127.0.0.1:8080/"
KEYCLOAK_REALM = "calendar-realm"
KEYCLOAK_CLIENT = "calendar-client"

@pytest.fixture(scope="session")
def access_token():
    resp = requests.post(
        f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
        data={
            "client_id": KEYCLOAK_CLIENT,
            "grant_type": "password",
            "username": "alin",
            "password": "alin123",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }