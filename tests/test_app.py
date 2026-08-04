from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def isolate_activities_state():
    original_state = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_state)


def _encode_path(value: str) -> str:
    return quote(value, safe="")


def test_get_activities_returns_expected_structure(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert expected_activity in payload
    assert "description" in payload[expected_activity]
    assert "schedule" in payload[expected_activity]
    assert "max_participants" in payload[expected_activity]
    assert "participants" in payload[expected_activity]


def test_signup_registers_participant_successfully(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "new.student@mergington.edu"
    previous_total = len(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{_encode_path(activity_name)}/signup",
        params={"email": new_email},
    )
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == previous_total + 1


def test_signup_returns_400_when_participant_already_registered(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{_encode_path(activity_name)}/signup",
        params={"email": existing_email},
    )
    payload = response.json()

    # Assert
    assert response.status_code == 400
    assert payload["detail"] == "Student already signed up for this activity"


def test_signup_returns_404_when_activity_does_not_exist(client):
    # Arrange
    invalid_activity = "Science Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{_encode_path(invalid_activity)}/signup",
        params={"email": email},
    )
    payload = response.json()

    # Assert
    assert response.status_code == 404
    assert payload["detail"] == "Activity not found"


def test_unregister_removes_participant_successfully(client):
    # Arrange
    activity_name = "Chess Club"
    participant_email = "daniel@mergington.edu"
    previous_total = len(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{_encode_path(activity_name)}/participants/{_encode_path(participant_email)}"
    )
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["message"] == f"Unregistered {participant_email} from {activity_name}"
    assert participant_email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == previous_total - 1


def test_unregister_returns_404_when_participant_not_in_activity(client):
    # Arrange
    activity_name = "Chess Club"
    unknown_email = "not.registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{_encode_path(activity_name)}/participants/{_encode_path(unknown_email)}"
    )
    payload = response.json()

    # Assert
    assert response.status_code == 404
    assert payload["detail"] == "Participant not found in this activity"


def test_unregister_returns_404_when_activity_does_not_exist(client):
    # Arrange
    invalid_activity = "Science Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{_encode_path(invalid_activity)}/participants/{_encode_path(email)}"
    )
    payload = response.json()

    # Assert
    assert response.status_code == 404
    assert payload["detail"] == "Activity not found"
