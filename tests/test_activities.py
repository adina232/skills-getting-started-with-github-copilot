"""Tests for the activities API endpoints using AAA pattern."""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities with correct structure."""
        # Arrange
        expected_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(activities, dict)
        assert len(activities) > 0
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert expected_keys.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self):
        """Test successful signup for an activity."""
        # Arrange
        test_email = "new_signup@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email},
        )
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert test_email in data["message"]
        assert activity_name in data["message"]

    def test_signup_duplicate_registration(self):
        """Test that duplicate signup returns 400 error."""
        # Arrange
        test_email = "duplicate_test@mergington.edu"
        activity_name = "Programming Class"

        # Act - First signup
        response_first = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email},
        )

        # Act - Second signup with same email
        response_second = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email},
        )

        # Assert
        assert response_first.status_code == 200
        assert response_second.status_code == 400
        assert "already signed up" in response_second.json()["detail"]

    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity returns 404."""
        # Arrange
        test_email = "test@mergington.edu"
        invalid_activity = "Non-Existent Activity"

        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_fills_available_spot(self):
        """Test that signup correctly adds participant to activity."""
        # Arrange
        test_email = "spot_filler@mergington.edu"
        activity_name = "Art Workshop"

        # Act - Get initial participant count
        response_before = client.get("/activities")
        participants_before = len(response_before.json()[activity_name]["participants"])

        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email},
        )

        # Act - Get updated participant count
        response_after = client.get("/activities")
        participants_after = len(response_after.json()[activity_name]["participants"])

        # Assert
        assert signup_response.status_code == 200
        assert participants_after == participants_before + 1
        assert test_email in response_after.json()[activity_name]["participants"]


class TestUnregisterParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""

    def test_unregister_success(self):
        """Test successful unregistration from an activity."""
        # Arrange
        test_email = "unregister_success@mergington.edu"
        activity_name = "Drama Club"

        # Act - Sign up first
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email},
        )

        # Act - Unregister
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": test_email},
        )
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert test_email in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant from the list."""
        # Arrange
        test_email = "participant_removal@mergington.edu"
        activity_name = "Science Club"

        # Act - Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email},
        )

        # Act - Get participants before unregister
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity_name]["participants"]

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": test_email},
        )

        # Act - Get participants after unregister
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]

        # Assert
        assert unregister_response.status_code == 200
        assert test_email in participants_before
        assert test_email not in participants_after

    def test_unregister_nonexistent_participant(self):
        """Test unregistering a participant who was never registered."""
        # Arrange
        test_email = "never_registered@mergington.edu"
        activity_name = "Book Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_from_invalid_activity(self):
        """Test unregistering from non-existent activity returns 404."""
        # Arrange
        test_email = "test@mergington.edu"
        invalid_activity = "Non-Existent Activity"

        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/participants",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
