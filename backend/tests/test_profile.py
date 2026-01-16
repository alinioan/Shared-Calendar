import pytest
import requests

PROFILE_API = "http://127.0.0.1:5002"

def test_get_profile_found(auth_headers):
    url = f"{PROFILE_API}/profile/"
    response = requests.get(url, headers=auth_headers)
    assert response.status_code == 200, f"expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "keycloak_id" in data
    assert "email" in data
    assert "full_name" in data
    assert "role" in data

def test_get_user_profile_found(auth_headers):
    url = f"{PROFILE_API}/profile/user"
    payload = {
        "email": "bob@example.com"
    }
    response = requests.get(url, headers=auth_headers, json=payload)
    assert response.status_code == 200, f"expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "keycloak_id" in data
    assert "email" in data
    assert "full_name" in data
    assert "role" in data

def test_get_user_profile_not_found(auth_headers):
    url = f"{PROFILE_API}/profile/user"
    payload = {
        "email": "nonexistent@example.com"
    }
    response = requests.get(url, headers=auth_headers, json=payload)
    assert response.status_code == 404, f"expected 404, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["error"] == "Profile not found. Run /sync first."