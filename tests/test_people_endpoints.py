import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from src.models.person import Person
from src.schemas.person import PersonCreate, PersonUpdate


class TestPeopleEndpoints:
    @pytest.fixture
    def sample_person_data(self):
        """Create sample person data for testing."""
        return {
            "login_id": "jdoe",
            "person_id": "12345",
            "name_first": "John",
            "name_middle": "Q",
            "name_last": "Doe"
        }

    @pytest.fixture
    def another_person_data(self):
        """Create another person data for testing."""
        return {
            "login_id": "jsmith",
            "person_id": "67890",
            "name_first": "Jane",
            "name_middle": "A",
            "name_last": "Smith"
        }


class TestCreatePerson(TestPeopleEndpoints):
    def test_create_person_success(self, test_client, sample_person_data):
        """Test successful person creation."""
        response = test_client.post("/people/", json=sample_person_data)

        assert response.status_code == 201
        data = response.json()
        assert data["login_id"] == "jdoe"
        assert data["person_id"] == "12345"
        assert data["name_first"] == "John"
        assert data["name_last"] == "Doe"
        assert "id" in data
        assert "created_at" in data

    def test_create_person_duplicate_mayo_login_id(self, test_client, sample_person_data):
        """Test person creation with duplicate login_id."""
        # First create a person
        response = test_client.post("/people/", json=sample_person_data)
        assert response.status_code == 201

        # Try to create another person with the same login_id
        response = test_client.post("/people/", json=sample_person_data)

        assert response.status_code == 409
        assert "login_id" in response.json()["detail"]
        assert "already exists" in response.json()["detail"]

    def test_create_person_duplicate_mayo_person_id(self, test_client, sample_person_data, another_person_data):
        """Test person creation with duplicate person_id."""
        # First create a person
        response = test_client.post("/people/", json=sample_person_data)
        assert response.status_code == 201

        # Try to create another person with different login but same person ID
        another_person_data["person_id"] = sample_person_data["person_id"]
        response = test_client.post("/people/", json=another_person_data)

        assert response.status_code == 409
        assert "person_id" in response.json()["detail"]
        assert "already exists" in response.json()["detail"]

    def test_create_person_invalid_data(self, test_client):
        """Test person creation with invalid data."""
        # Since all fields have defaults, let's test with invalid data type
        invalid_data = {
            "login_id": 123,  # Should be string
            "person_id": "valid"
        }

        response = test_client.post("/people/", json=invalid_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_create_person_service_error(self, test_client, sample_person_data):
        """Test person creation with service ValueError (covers line 51)."""
        from src.main import app
        from src.routers.people import get_person_service
        from unittest.mock import MagicMock

        # Create a mock service that raises ValueError
        mock_service = MagicMock()
        mock_service.get_person_by_mayo_login_id.return_value = None
        mock_service.get_person_by_mayo_person_id.return_value = None
        mock_service.create_person.side_effect = ValueError("Database constraint violation")

        # Override the service dependency
        app.dependency_overrides[get_person_service] = lambda: mock_service

        try:
            response = test_client.post("/people/", json=sample_person_data)

            assert response.status_code == 400
            assert "Database constraint violation" in response.json()["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.pop(get_person_service, None)


class TestGetPeople(TestPeopleEndpoints):
    def test_get_people_empty(self, test_client):
        """Test getting people when database is empty."""
        response = test_client.get("/people/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_people_with_data(self, test_client, sample_person_data, another_person_data):
        """Test getting people with data in database."""
        # Create two people
        test_client.post("/people/", json=sample_person_data)
        test_client.post("/people/", json=another_person_data)

        response = test_client.get("/people/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_people_with_pagination(self, test_client, sample_person_data):
        """Test getting people with pagination parameters."""
        # Create a person
        test_client.post("/people/", json=sample_person_data)

        response = test_client.get("/people/?skip=0&limit=5")
        assert response.status_code == 200
        assert len(response.json()) >= 0

        response = test_client.get("/people/?skip=10&limit=5")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_people_with_name_search(self, test_client, sample_person_data, another_person_data):
        """Test getting people with name search."""
        # Create two people
        test_client.post("/people/", json=sample_person_data)
        test_client.post("/people/", json=another_person_data)

        response = test_client.get("/people/?name=John")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name_first"] == "John"

    def test_get_people_invalid_pagination(self, test_client):
        """Test getting people with invalid pagination parameters."""
        response = test_client.get("/people/?skip=-1")
        assert response.status_code == 422

        response = test_client.get("/people/?limit=0")
        assert response.status_code == 422

        response = test_client.get("/people/?limit=2000")
        assert response.status_code == 422


class TestGetPersonById(TestPeopleEndpoints):
    def test_get_person_by_id_success(self, test_client, sample_person_data):
        """Test getting person by ID successfully."""
        # Create a person
        create_response = test_client.post("/people/", json=sample_person_data)
        assert create_response.status_code == 201  # Ensure creation succeeded
        person_id = create_response.json()["id"]

        response = test_client.get(f"/people/{person_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == person_id
        assert data["login_id"] == "jdoe"

    def test_get_person_by_id_not_found(self, test_client):
        """Test getting person by ID when not found."""
        person_id = str(uuid.uuid4())
        response = test_client.get(f"/people/{person_id}")

        assert response.status_code == 404
        assert person_id in response.json()["detail"]

    def test_get_person_by_id_invalid_uuid(self, test_client):
        """Test getting person with non-existent ID."""
        # Since we use string IDs, any string is valid
        # This should return 404 for non-existent person
        response = test_client.get("/people/non-existent-id")

        assert response.status_code == 404


class TestUpdatePerson(TestPeopleEndpoints):
    def test_update_person_success(self, test_client, sample_person_data):
        """Test updating person successfully."""
        # Create a person
        create_response = test_client.post("/people/", json=sample_person_data)
        person_id = create_response.json()["id"]

        update_data = {"name_first": "Jane"}
        response = test_client.put(f"/people/{person_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name_first"] == "Jane"
        assert data["name_last"] == "Doe"  # Unchanged

    def test_update_person_not_found(self, test_client):
        """Test updating person when not found."""
        person_id = str(uuid.uuid4())
        update_data = {"name_first": "Jane"}
        response = test_client.put(f"/people/{person_id}", json=update_data)

        assert response.status_code == 404
        assert person_id in response.json()["detail"]

    def test_update_person_duplicate_mayo_login_id(self, test_client, sample_person_data, another_person_data):
        """Test updating person with duplicate login_id."""
        # Create two people
        create_response1 = test_client.post("/people/", json=sample_person_data)
        create_response2 = test_client.post("/people/", json=another_person_data)
        person_id = create_response1.json()["id"]

        # Try to update first person with second person's login_id
        update_data = {"login_id": another_person_data["login_id"]}
        response = test_client.put(f"/people/{person_id}", json=update_data)

        assert response.status_code == 409
        assert "login_id" in response.json()["detail"]

    def test_update_person_duplicate_mayo_person_id(self, test_client, sample_person_data, another_person_data):
        """Test updating person with duplicate person_id (covers lines 129-131)."""
        # Create two people
        create_response1 = test_client.post("/people/", json=sample_person_data)
        create_response2 = test_client.post("/people/", json=another_person_data)
        person_id = create_response1.json()["id"]

        # Try to update first person with second person's person_id
        update_data = {"person_id": another_person_data["person_id"]}
        response = test_client.put(f"/people/{person_id}", json=update_data)

        assert response.status_code == 409
        assert "person_id" in response.json()["detail"]
        assert "already exists" in response.json()["detail"]

    def test_update_person_service_error(self, test_client, sample_person_data):
        """Test updating person with service ValueError (covers line 139)."""
        from src.main import app
        from src.routers.people import get_person_service
        from unittest.mock import MagicMock

        # Create a person first
        create_response = test_client.post("/people/", json=sample_person_data)
        person_id = create_response.json()["id"]

        # Create a mock service that raises ValueError
        mock_service = MagicMock()
        mock_service.get_person_by_mayo_login_id.return_value = None
        mock_service.get_person_by_mayo_person_id.return_value = None
        mock_service.update_person.side_effect = ValueError("Database constraint violation")

        # Override the service dependency
        app.dependency_overrides[get_person_service] = lambda: mock_service

        try:
            update_data = {"name_first": "UpdatedName"}
            response = test_client.put(f"/people/{person_id}", json=update_data)

            assert response.status_code == 400
            assert "Database constraint violation" in response.json()["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.pop(get_person_service, None)


class TestDeletePerson(TestPeopleEndpoints):
    def test_delete_person_success(self, test_client, sample_person_data):
        """Test deleting person successfully."""
        # Create a person
        create_response = test_client.post("/people/", json=sample_person_data)
        person_id = create_response.json()["id"]

        response = test_client.delete(f"/people/{person_id}")

        assert response.status_code == 204
        assert response.text == ""

        # Verify person is deleted
        get_response = test_client.get(f"/people/{person_id}")
        assert get_response.status_code == 404

    def test_delete_person_not_found(self, test_client):
        """Test deleting person when not found."""
        person_id = str(uuid.uuid4())
        response = test_client.delete(f"/people/{person_id}")

        assert response.status_code == 404
        assert person_id in response.json()["detail"]


class TestGetPersonByMayoIds(TestPeopleEndpoints):
    def test_get_person_by_mayo_login_id_success(self, test_client, sample_person_data):
        """Test getting person by login_id successfully."""
        # Create a person
        test_client.post("/people/", json=sample_person_data)

        response = test_client.get(f"/people/mayo-login/{sample_person_data['login_id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["login_id"] == sample_person_data["login_id"]

    def test_get_person_by_mayo_login_id_not_found(self, test_client):
        """Test getting person by login_id when not found."""
        response = test_client.get("/people/mayo-login/nonexistent")

        assert response.status_code == 404
        assert "nonexistent" in response.json()["detail"]

    def test_get_person_by_mayo_person_id_success(self, test_client, sample_person_data):
        """Test getting person by person_id successfully."""
        # Create a person
        test_client.post("/people/", json=sample_person_data)

        response = test_client.get(f"/people/mayo-person/{sample_person_data['person_id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["person_id"] == sample_person_data["person_id"]

    def test_get_person_by_mayo_person_id_not_found(self, test_client):
        """Test getting person by person_id when not found."""
        response = test_client.get("/people/mayo-person/99999")

        assert response.status_code == 404
        assert "99999" in response.json()["detail"]


class TestPeopleStats(TestPeopleEndpoints):
    def test_get_people_count(self, test_client, sample_person_data, another_person_data):
        """Test getting people count."""
        # Create two people
        test_client.post("/people/", json=sample_person_data)
        test_client.post("/people/", json=another_person_data)

        response = test_client.get("/people/stats/count")

        assert response.status_code == 200
        data = response.json()
        assert data["total_people"] == 2


class TestEndpointIntegration(TestPeopleEndpoints):
    def test_endpoints_included_in_app(self, test_client):
        """Test that people endpoints are properly included in the app."""
        # Test that the routes exist by checking 405 (method not allowed) vs 404 (not found)
        response = test_client.post("/people/stats/count")  # Wrong method for this endpoint
        assert response.status_code == 405  # Method not allowed (route exists)

        response = test_client.get("/nonexistent-base-path/test")
        assert response.status_code == 404  # Not found (route doesn't exist)

    def test_openapi_includes_people_endpoints(self, test_client):
        """Test that OpenAPI spec includes people endpoints."""
        response = test_client.get("/openapi.json")
        openapi_spec = response.json()

        # Check that people endpoints are documented
        paths = openapi_spec["paths"]
        assert "/people/" in paths
        assert "/people/{person_id}" in paths
        assert "/people/mayo-login/{login_id}" in paths
        assert "/people/mayo-person/{person_id}" in paths
        assert "/people/stats/count" in paths

        # Check that people operations have the correct tag
        people_operations = []
        for path, methods in paths.items():
            if "/people" in path:
                for method, operation in methods.items():
                    if "tags" in operation:
                        people_operations.extend(operation["tags"])

        assert "people" in people_operations