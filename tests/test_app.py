import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)

ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield


def test_root_redirects_to_static():
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    # Arrange
    url = "/activities"

    # Act
    response = client.get(url)
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert isinstance(payload, dict)
    assert "Chess Club" in payload
    assert "participants" in payload["Chess Club"]
    assert isinstance(payload["Chess Club"]["participants"], list)


def test_signup_adds_new_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "alex_new@mergington.edu"
    signup_url = f"/activities/{activity_name}/signup?email={email}"

    # Act
    response = client.post(signup_url)
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["message"] == f"Signed up {email} for {activity_name}"
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "duplicate_test@mergington.edu"
    signup_url = f"/activities/{activity_name}/signup?email={email}"

    # Act
    first_response = client.post(signup_url)
    second_response = client.post(signup_url)
    second_payload = second_response.json()

    # Assert
    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_payload["detail"] == "Student already signed up for this activity"
    assert app_module.activities[activity_name]["participants"].count(email) == 1


def test_remove_participant_removes_existing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    delete_url = f"/activities/{activity_name}/participants?email={email}"

    # Act
    response = client.delete(delete_url)
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["message"] == f"Removed {email} from {activity_name}"
    assert email not in app_module.activities[activity_name]["participants"]


def test_remove_nonexistent_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    email = "nobody@mergington.edu"
    delete_url = f"/activities/{activity_name}/participants?email={email}"

    # Act
    response = client.delete(delete_url)
    payload = response.json()

    # Assert
    assert response.status_code == 404
    assert payload["detail"] == "Participant not found in activity"
