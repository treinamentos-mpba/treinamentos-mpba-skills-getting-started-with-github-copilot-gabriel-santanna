from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_activities = deepcopy(app_module.activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "student@mergington.edu"
    expected_participants = deepcopy(
        app_module.activities[activity_name]["participants"]
    )
    expected_participants.append(email)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert app_module.activities[activity_name]["participants"] == expected_participants


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    expected_participants = deepcopy(
        app_module.activities[activity_name]["participants"]
    )

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert app_module.activities[activity_name]["participants"] == expected_participants


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    expected_participants = deepcopy(
        app_module.activities[activity_name]["participants"]
    )
    expected_participants.remove(email)

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert app_module.activities[activity_name]["participants"] == expected_participants


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert app_module.activities[activity_name]["participants"] == []


@pytest.mark.parametrize("method", ["post", "delete"])
def test_signup_routes_return_404_for_unknown_activity(client, method):
    # Arrange
    activity_name = "Unknown Club"
    request = getattr(client, method)

    # Act
    response = request(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


@pytest.mark.parametrize("method", ["post", "delete"])
def test_signup_routes_require_email(client, method):
    # Arrange
    request = getattr(client, method)

    # Act
    response = request("/activities/Soccer%20Club/signup")

    # Assert
    assert response.status_code == 422