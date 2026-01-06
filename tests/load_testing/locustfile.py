"""
Load testing script using Locust.

This script simulates high traffic to the survey platform to test performance
under stress. It includes scenarios for:
- Creating surveys
- Retrieving public surveys
- Submitting partial responses (heartbeat)
- Submitting final responses
- Viewing responses

Usage:
    locust -f tests/load_testing/locustfile.py --host=http://localhost:8000

    # For headless mode with specific users and spawn rate:
    locust -f tests/load_testing/locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 5m --headless
"""
import json
import random
import uuid

from locust import HttpUser, between, task


class SurveyUser(HttpUser):
    """
    Simulates a user interacting with the survey platform.
    
    Weight distribution:
    - 60% survey takers (viewing and submitting)
    - 30% survey creators/managers
    - 10% analysts viewing responses
    """
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Initialize user session."""
        self.session_token = str(uuid.uuid4())
        self.survey_id = None
        self.field_ids = []
        
        # Randomly assign user role
        role_choice = random.random()
        if role_choice < 0.6:
            self.role = "taker"
            self.setup_survey_taker()
        elif role_choice < 0.9:
            self.role = "creator"
            self.setup_survey_creator()
        else:
            self.role = "analyst"
            self.setup_analyst()
    
    def setup_survey_taker(self):
        """Setup for survey takers (no auth needed)."""
        # Get a random active survey
        response = self.client.get("/api/v1/surveys/", catch_response=True)
        if response.status_code == 200:
            surveys = response.json().get("results", [])
            if surveys:
                self.survey_id = surveys[0]["id"]
    
    def setup_survey_creator(self):
        """Setup for survey creators (requires auth)."""
        # Create or login as admin
        email = f"admin_{random.randint(1, 100)}@example.com"
        password = "testpass123"
        
        # Try to login
        response = self.client.post("/api/v1/auth/login/", json={
            "email": email,
            "password": password
        }, catch_response=True)
        
        if response.status_code == 200:
            token = response.json().get("access")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    def setup_analyst(self):
        """Setup for analysts (requires auth)."""
        # Similar to creator but with analyst role
        email = f"analyst_{random.randint(1, 50)}@example.com"
        password = "testpass123"
        
        response = self.client.post("/api/v1/auth/login/", json={
            "email": email,
            "password": password
        }, catch_response=True)
        
        if response.status_code == 200:
            token = response.json().get("access")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(10)
    def view_public_survey(self):
        """View a public survey (most common operation)."""
        if not self.survey_id:
            # Get first available survey
            response = self.client.get("/api/v1/surveys/")
            if response.status_code == 200:
                surveys = response.json().get("results", [])
                if surveys:
                    self.survey_id = surveys[0]["id"]
        
        if self.survey_id:
            with self.client.get(
                f"/api/v1/public/surveys/{self.survey_id}/",
                catch_response=True,
                name="/api/v1/public/surveys/[id]/"
            ) as response:
                if response.status_code == 200:
                    # Extract field IDs for later use
                    data = response.json()
                    for section in data.get("sections", []):
                        for field in section.get("fields", []):
                            self.field_ids.append(field["id"])
                    response.success()
                else:
                    response.failure(f"Failed to get survey: {response.status_code}")
    
    @task(5)
    def save_partial_response(self):
        """Save partial response (heartbeat)."""
        if not self.survey_id or not self.field_ids:
            return
        
        # Generate partial data
        partial_data = {}
        for field_id in random.sample(self.field_ids, min(3, len(self.field_ids))):
            partial_data[field_id] = f"partial_value_{random.randint(1, 1000)}"
        
        with self.client.post(
            f"/api/v1/surveys/{self.survey_id}/partial/",
            json={
                "session_token": self.session_token,
                "data": partial_data
            },
            catch_response=True,
            name="/api/v1/surveys/[id]/partial/"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Failed to save partial: {response.status_code}")
    
    @task(3)
    def submit_survey(self):
        """Submit complete survey response."""
        if not self.survey_id or not self.field_ids:
            return
        
        # Generate complete data
        complete_data = {}
        for field_id in self.field_ids:
            complete_data[field_id] = f"value_{random.randint(1, 1000)}"
        
        with self.client.post(
            f"/api/v1/surveys/{self.survey_id}/submit/",
            json={
                "session_token": self.session_token,
                "data": complete_data
            },
            catch_response=True,
            name="/api/v1/surveys/[id]/submit/"
        ) as response:
            if response.status_code == 201:
                response.success()
                # Generate new session token for next submission
                self.session_token = str(uuid.uuid4())
            else:
                response.failure(f"Failed to submit: {response.status_code}")
    
    @task(2)
    def list_surveys(self):
        """List all surveys (authenticated users)."""
        if self.role in ["creator", "analyst"]:
            with self.client.get(
                "/api/v1/surveys/",
                catch_response=True,
                name="/api/v1/surveys/"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed to list surveys: {response.status_code}")
    
    @task(1)
    def create_survey(self):
        """Create a new survey (creators only)."""
        if self.role != "creator":
            return
        
        survey_data = {
            "title": f"Load Test Survey {random.randint(1, 10000)}",
            "description": "Survey created during load testing",
            "is_active": True,
            "sections": [
                {
                    "title": "Section 1",
                    "description": "Test section",
                    "order": 0,
                    "fields": [
                        {
                            "field_type": "text",
                            "label": "Name",
                            "is_required": True,
                            "order": 0
                        },
                        {
                            "field_type": "email",
                            "label": "Email",
                            "is_required": True,
                            "order": 1
                        }
                    ]
                }
            ]
        }
        
        with self.client.post(
            "/api/v1/surveys/",
            json=survey_data,
            catch_response=True,
            name="/api/v1/surveys/ [POST]"
        ) as response:
            if response.status_code == 201:
                response.success()
                # Store the created survey ID
                self.survey_id = response.json()["id"]
            else:
                response.failure(f"Failed to create survey: {response.status_code}")
    
    @task(2)
    def view_responses(self):
        """View survey responses (analysts and creators)."""
        if self.role not in ["creator", "analyst"] or not self.survey_id:
            return
        
        with self.client.get(
            f"/api/v1/surveys/{self.survey_id}/responses/",
            catch_response=True,
            name="/api/v1/surveys/[id]/responses/"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to view responses: {response.status_code}")


class StressTestUser(HttpUser):
    """
    Aggressive stress testing user.
    
    Simulates extreme load with rapid requests to test system limits.
    """
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    def on_start(self):
        """Initialize stress test session."""
        self.survey_id = None
        self.session_token = str(uuid.uuid4())
    
    @task(20)
    def rapid_public_survey_access(self):
        """Rapidly access public surveys."""
        # Get a survey ID
        if not self.survey_id:
            response = self.client.get("/api/v1/surveys/")
            if response.status_code == 200:
                surveys = response.json().get("results", [])
                if surveys:
                    self.survey_id = surveys[0]["id"]
        
        if self.survey_id:
            self.client.get(
                f"/api/v1/public/surveys/{self.survey_id}/",
                name="/api/v1/public/surveys/[id]/ [STRESS]"
            )
    
    @task(10)
    def rapid_partial_saves(self):
        """Rapidly save partial responses."""
        if not self.survey_id:
            return
        
        self.client.post(
            f"/api/v1/surveys/{self.survey_id}/partial/",
            json={
                "session_token": self.session_token,
                "data": {"field": f"stress_value_{random.randint(1, 1000)}"}
            },
            name="/api/v1/surveys/[id]/partial/ [STRESS]"
        )
