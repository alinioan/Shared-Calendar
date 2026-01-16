import requests
import pytest
import time
from datetime import datetime, timedelta

CALENDAR_API = "http://127.0.0.1:5000"

@pytest.fixture(scope="session")
def job_id(auth_headers):
    group_id = 1
    payload = {
        "duration": {
            "hours": 1,
            "minutes": 0
        },
        "start_time": "2026-01-01T08:00:00",
        "end_time": "2026-01-01T18:00:00"
    }
    resp = requests.post(
        f"{CALENDAR_API}/events/recommendations/group/{group_id}",
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 202, f"expected 202, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "job_id" in body
    assert body.get("status") == "submitted"
    return body["job_id"]

def test_intervals(auth_headers, job_id):
    group_id = 1
    resp = requests.get(
        f"{CALENDAR_API}/events/recommendations/group/{group_id}/job/{job_id}",
        headers=auth_headers
    )

    assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}"
    
    body = resp.json()
    intervals = body["intervals"]

    assert len(intervals) == 5
    
    assert intervals[0]["start_time"] == "Thu, 01 Jan 2026 10:00:00 GMT"
    assert intervals[0]["end_time"] == "Thu, 01 Jan 2026 11:00:00 GMT"

    assert intervals[1]["start_time"] == "Thu, 01 Jan 2026 11:00:00 GMT"
    assert intervals[1]["end_time"] == "Thu, 01 Jan 2026 12:00:00 GMT"

    assert intervals[2]["start_time"] == "Thu, 01 Jan 2026 13:00:00 GMT"
    assert intervals[2]["end_time"] == "Thu, 01 Jan 2026 14:00:00 GMT"