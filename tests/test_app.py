"""Tests for the Mergington High School API."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a clean state before each test."""
    from src.app import activities
    
    # Store original state
    original_activities = {k: v.copy() for k, v in activities.items()}
    original_activities = {
        k: {**v, "participants": v["participants"].copy()} 
        for k, v in original_activities.items()
    }
    
    yield
    
    # Reset after test
    for activity_name in activities:
        activities[activity_name]["participants"] = original_activities[activity_name]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities(self, client):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Basketball" in data
        assert "Chess Club" in data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
    
    def test_activities_with_participants(self, client):
        """Test that some activities have pre-populated participants."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club and Programming Class should have participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert len(data["Gym Class"]["participants"]) == 2


class TestSignUpForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert "student@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant."""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Basketball"]["participants"])
        
        # Signup
        client.post(
            "/activities/Basketball/signup",
            params={"email": "new.student@mergington.edu"}
        )
        
        # Check updated count
        response = client.get("/activities")
        new_count = len(response.json()["Basketball"]["participants"])
        assert new_count == initial_count + 1
        assert "new.student@mergington.edu" in response.json()["Basketball"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for a non-existent activity."""
        response = client.post(
            "/activities/NonExistent/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that duplicate signups are rejected."""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test signing up for multiple different activities."""
        email = "student@mergington.edu"
        
        response1 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Tennis/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        assert email in response.json()["Basketball"]["participants"]
        assert email in response.json()["Tennis"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"
        
        # Verify participant is there
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        email = "michael@mergington.edu"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Unregister
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        # Check updated count
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count - 1
        assert email not in response.json()["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from a non-existent activity."""
        response = client.delete(
            "/activities/NonExistent/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregistering someone not signed up."""
        response = client.delete(
            "/activities/Basketball/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a participant can unregister and sign up again."""
        email = "student@mergington.edu"
        
        # Sign up
        response1 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(
            "/activities/Basketball/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify in list
        response = client.get("/activities")
        assert email in response.json()["Basketball"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint."""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static index."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests combining multiple endpoints."""
    
    def test_full_user_flow(self, client, reset_activities):
        """Test a complete user flow: view activities, signup, unregister."""
        email = "integration.test@mergington.edu"
        
        # 1. Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        initial_basketball_count = len(activities_data["Basketball"]["participants"])
        
        # 2. Sign up for activity
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # 3. Verify signup
        response = client.get("/activities")
        new_basketball_count = len(response.json()["Basketball"]["participants"])
        assert new_basketball_count == initial_basketball_count + 1
        
        # 4. Unregister
        response = client.delete(
            "/activities/Basketball/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # 5. Verify unregister
        response = client.get("/activities")
        final_basketball_count = len(response.json()["Basketball"]["participants"])
        assert final_basketball_count == initial_basketball_count
