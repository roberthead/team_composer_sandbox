import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.main import app, read_root


class TestFastAPIApp:
    def test_app_instance_creation(self):
        """Test FastAPI app instance is created correctly."""
        assert isinstance(app, FastAPI)
        assert app is not None
    
    def test_app_title_configured(self):
        """Test FastAPI app has configured title."""
        assert hasattr(app, 'title')
        assert app.title == "Person Management API"
    
    def test_app_version_configured(self):
        """Test FastAPI app has configured version."""
        assert hasattr(app, 'version')
        assert app.version == "1.0.0"


class TestRootEndpoint:
    def test_read_root_function_exists(self):
        """Test read_root function is defined."""
        assert callable(read_root)
    
    def test_read_root_return_value(self):
        """Test read_root returns correct response."""
        response = read_root()
        
        assert response == {"Hello": "World"}
        assert isinstance(response, dict)
        assert "Hello" in response
        assert response["Hello"] == "World"


class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    def test_root_endpoint_get(self, client):
        """Test GET request to root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"Hello": "World"}
    
    def test_root_endpoint_content_type(self, client):
        """Test root endpoint returns JSON content type."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_root_endpoint_response_structure(self, client):
        """Test root endpoint response structure."""
        response = client.get("/")
        json_response = response.json()
        
        assert isinstance(json_response, dict)
        assert len(json_response) == 1
        assert "Hello" in json_response
        assert isinstance(json_response["Hello"], str)
    
    def test_nonexistent_endpoint_404(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
        assert "detail" in response.json()
        assert response.json()["detail"] == "Not Found"
    
    def test_root_endpoint_method_not_allowed(self, client):
        """Test root endpoint with unsupported HTTP methods."""
        # POST to root should return 405 Method Not Allowed
        response = client.post("/")
        assert response.status_code == 405
        
        # PUT to root should return 405 Method Not Allowed
        response = client.put("/")
        assert response.status_code == 405
        
        # DELETE to root should return 405 Method Not Allowed
        response = client.delete("/")
        assert response.status_code == 405
    
    def test_root_endpoint_options_method(self, client):
        """Test OPTIONS method on root endpoint."""
        response = client.options("/")
        
        # OPTIONS should be allowed for CORS purposes
        assert response.status_code in [200, 405]  # Either allowed or not implemented
    
    def test_root_endpoint_head_method(self, client):
        """Test HEAD method on root endpoint."""
        response = client.head("/")
        
        # HEAD may or may not be implemented - both 200 and 405 are acceptable
        assert response.status_code in [200, 405]
        if response.status_code == 200:
            assert response.text == ""  # No body for HEAD requests


class TestAPIDocumentation:
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    def test_openapi_docs_available(self, client):
        """Test that OpenAPI documentation is available."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_docs_available(self, client):
        """Test that ReDoc documentation is available."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_json_available(self, client):
        """Test that OpenAPI JSON specification is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert "paths" in openapi_spec
    
    def test_openapi_spec_contains_root_endpoint(self, client):
        """Test that OpenAPI spec documents the root endpoint."""
        response = client.get("/openapi.json")
        openapi_spec = response.json()
        
        assert "/" in openapi_spec["paths"]
        assert "get" in openapi_spec["paths"]["/"]
        
        root_endpoint = openapi_spec["paths"]["/"]["get"]
        assert "responses" in root_endpoint
        assert "200" in root_endpoint["responses"]


class TestApplicationConfiguration:
    def test_app_routes_registered(self):
        """Test that routes are properly registered with the app."""
        routes = app.routes
        
        # Should have at least one route (our root endpoint)
        assert len(routes) >= 1
        
        # Find our root route
        root_routes = [route for route in routes if hasattr(route, 'path') and route.path == "/"]
        assert len(root_routes) >= 1
        
        root_route = root_routes[0]
        assert "GET" in root_route.methods
    
    def test_app_middleware_stack(self):
        """Test app middleware configuration."""
        # Check that middleware stack exists and is properly configured
        assert hasattr(app, 'middleware_stack')
        assert app.middleware_stack is not None
    
    def test_app_exception_handlers(self):
        """Test app has default exception handlers."""
        assert hasattr(app, 'exception_handlers')
        assert isinstance(app.exception_handlers, dict)


class TestApplicationHealth:
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    def test_app_startup_successful(self, client):
        """Test that the application starts up successfully."""
        # Making any request should work if app started correctly
        response = client.get("/")
        assert response.status_code == 200
    
    def test_app_handles_concurrent_requests(self, client):
        """Test app can handle multiple concurrent requests."""
        import concurrent.futures
        
        def make_request():
            return client.get("/")
        
        # Test with multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                assert response.json() == {"Hello": "World"}
    
    def test_app_response_consistency(self, client):
        """Test that repeated requests return consistent responses."""
        responses = []
        
        for _ in range(5):
            response = client.get("/")
            responses.append(response.json())
        
        # All responses should be identical
        first_response = responses[0]
        for response in responses[1:]:
            assert response == first_response


class TestApplicationIntegration:
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    def test_app_with_dependency_injection_ready(self):
        """Test app is ready for dependency injection (future endpoints)."""
        # Verify that the app can handle dependency injection
        # This is important for future database-connected endpoints
        assert hasattr(app, 'dependency_overrides')
        assert isinstance(app.dependency_overrides, dict)
    
    def test_app_cors_ready(self, client):
        """Test app is ready for CORS if needed in the future."""
        response = client.get("/")
        
        # Basic request should work (CORS middleware can be added later)
        assert response.status_code == 200
    
    def test_app_can_be_extended(self):
        """Test that the app can be extended with additional routers."""
        from fastapi import APIRouter
        
        # Create a test router
        test_router = APIRouter()
        
        @test_router.get("/test")
        def test_endpoint():
            return {"test": "endpoint"}
        
        # Should be able to include the router
        try:
            app.include_router(test_router)
            # If we get here, the app can be extended
            assert True
        except Exception as e:
            pytest.fail(f"App should be extensible with routers: {e}")
        finally:
            # Clean up - remove the test router
            if test_router in getattr(app, 'router', {}).routes if hasattr(app, 'router') else []:
                app.router.routes.remove(test_router)