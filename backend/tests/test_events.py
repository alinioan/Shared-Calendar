from concurrent.futures import ThreadPoolExecutor
import requests
import pytest
import time
from datetime import datetime, timedelta

CALENDAR_API = "http://127.0.0.1:5000"
GROUP_ID = 1

@pytest.fixture(scope="session")
def event_id(auth_headers):
    start_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    end_time = (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"

    event_resp = requests.post(
        f"{CALENDAR_API}/events/group/{GROUP_ID}",
        json={
            "title": "Test Event python",
            "description": "This is a test event with pytest",
            "start_time": start_time,
            "end_time": end_time
        },
        headers=auth_headers,
    )

    assert event_resp.status_code == 201
    event_data = event_resp.json()
    assert event_data["title"] == "Test Event python"
    assert event_data["description"] == "This is a test event with pytest"

    return event_data["id"]

def test_get_group_events(auth_headers):
    events_resp = requests.get(
        f"{CALENDAR_API}/events/group/{GROUP_ID}",
        headers=auth_headers,
    )

    assert events_resp.status_code == 200
    events_data = events_resp.json()
    assert "events" in events_data
    assert isinstance(events_data["events"], list)

def test_remove_event(auth_headers, event_id):
    remove_resp = requests.delete(
        f"{CALENDAR_API}/events/group/{GROUP_ID}",
        json={"event_id": event_id},
        headers=auth_headers,
    )

    print(remove_resp.text)
    assert remove_resp.status_code == 200
    remove_data = remove_resp.json()
    assert remove_data["message"] == "Event deleted successfully"

def test_create_overlapping_event(auth_headers):
    start_time = (datetime.utcnow() + timedelta(hours=3)).isoformat() + "Z"
    end_time = (datetime.utcnow() + timedelta(hours=4)).isoformat() + "Z"

    first_event_resp = requests.post(
        f"{CALENDAR_API}/events/group/{GROUP_ID}",
        json={
            "title": "First Event",
            "description": "This is the first event",
            "start_time": start_time,
            "end_time": end_time
        },
        headers=auth_headers,
    )

    assert first_event_resp.status_code == 201

    overlapping_event_resp = requests.post(
        f"{CALENDAR_API}/events/group/{GROUP_ID}",
        json={
            "title": "Overlapping Event",
            "description": "This event overlaps with the first event",
            "start_time": (datetime.utcnow() + timedelta(hours=3, minutes=30)).isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(hours=4, minutes=30)).isoformat() + "Z"
        },
        headers=auth_headers,
    )

    assert overlapping_event_resp.status_code == 400
    overlapping_data = overlapping_event_resp.json()
    assert overlapping_data["error"] == "Event time overlaps with an existing event"

    event_id = first_event_resp.json()["id"]

    remove_resp = requests.delete(
        f"{CALENDAR_API}/events/group/{GROUP_ID}",
        json={"event_id": event_id},
        headers=auth_headers,
    )

    assert remove_resp.status_code == 200
    remove_data = remove_resp.json()
    assert remove_data["message"] == "Event deleted successfully"

def test_concurent_events(auth_headers):
    start_time = (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z"
    end_time = (datetime.utcnow() + timedelta(hours=6)).isoformat() + "Z"

    def create_event():
        return requests.post(
            f"{CALENDAR_API}/events/group/{GROUP_ID}",
            json={
                "title": "Concurrent Write Event",
                "description": "Testing concurrent writes",
                "start_time": start_time,
                "end_time": end_time
            },
            headers=auth_headers,
        )

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(create_event),
            executor.submit(create_event),
        ]
        responses = [f.result() for f in futures]

    success_count = sum(1 for resp in responses if resp.status_code == 201)
    conflict_count = sum(1 for resp in responses if resp.status_code == 409)

    assert success_count == 1, "Only one event creation should succeed"
    assert conflict_count == 1, "Other event creations should fail with conflict"

    for resp in responses:
        if resp.status_code == 201:
            event_id = resp.json()["id"]
            remove_resp = requests.delete(
                f"{CALENDAR_API}/events/group/{GROUP_ID}",
                json={"event_id": event_id},
                headers=auth_headers,
            )
            assert remove_resp.status_code == 200
            remove_data = remove_resp.json()
            assert remove_data["message"] == "Event deleted successfully"