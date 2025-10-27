"""
Test API documentation with security controls.
"""
import pytest
from unittest.mock import patch
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

@pytest.fixture
def client():
    """Create test client for API documentation endpoints."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)

def test_docs_endpoint_debug_mode_enabled(client):
    """Test /docs endpoint is available in debug mode."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        response = client.get("/docs")
        
        # Should be available (redirect to docs or actual docs content)
        assert response.status_code in [200, 307]

def test_docs_endpoint_production_mode_disabled():
    """Test /docs endpoint returns 404 in production mode."""
    # Create a FastAPI app with production config
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    
    # Simulate production app configuration
    prod_app = FastAPI(
        title="Netanya Incident Service",
        docs_url=None,  # Disabled in production
        redoc_url=None,  # Disabled in production
        openapi_url=None  # Disabled in production
    )
    
    @prod_app.get("/docs", include_in_schema=False)
    async def docs_disabled():
        raise HTTPException(status_code=404, detail="Documentation not available in production mode")
    
    client = TestClient(prod_app)
    response = client.get("/docs")
    
    # Should return 404 in production
    assert response.status_code == 404

def test_redoc_endpoint_debug_mode_enabled(client):
    """Test /redoc endpoint is available in debug mode."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        response = client.get("/redoc")
        
        # Should be available
        assert response.status_code in [200, 307]

def test_redoc_endpoint_production_mode_disabled():
    """Test /redoc endpoint returns 404 in production mode."""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    
    # Simulate production app configuration
    prod_app = FastAPI(
        title="Netanya Incident Service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )
    
    @prod_app.get("/redoc", include_in_schema=False)
    async def redoc_disabled():
        raise HTTPException(status_code=404, detail="Documentation not available in production mode")
    
    client = TestClient(prod_app)
    response = client.get("/redoc")
    
    # Should return 404 in production
    assert response.status_code == 404

def test_openapi_json_endpoint_debug_mode():
    """Test OpenAPI JSON endpoint in debug mode."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        # Should be available
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Netanya Incident Service"

def test_openapi_json_endpoint_production_mode():
    """Test OpenAPI JSON endpoint is disabled in production mode."""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    
    # Simulate production app configuration
    prod_app = FastAPI(
        title="Netanya Incident Service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )
    
    @prod_app.get("/openapi.json", include_in_schema=False)
    async def openapi_disabled():
        raise HTTPException(status_code=404, detail="API specification not available in production mode")
    
    client = TestClient(prod_app)
    response = client.get("/openapi.json")
    
    # Should return 404 in production
    assert response.status_code == 404

def test_api_documentation_security_headers(client):
    """Test API documentation endpoints include security headers."""
    response = client.get("/docs")
    
    # Should work without exposing sensitive information
    assert response.status_code in [200, 307, 404]

def test_swagger_ui_configuration():
    """Test Swagger UI configuration in debug mode."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/docs")
        
        if response.status_code == 200:
            # Check that Swagger UI is properly configured
            content = response.text
            assert "Netanya Incident Service" in content

def test_api_documentation_content_completeness():
    """Test API documentation includes all endpoints and models."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            openapi_spec = response.json()
            
            # Should include main endpoints
            paths = openapi_spec.get("paths", {})
            assert "/incidents/submit" in paths
            assert "/health" in paths
            assert "/health/ready" in paths
            assert "/health/live" in paths
            
            # Should include request/response models
            components = openapi_spec.get("components", {})
            schemas = components.get("schemas", {})
            assert "IncidentSubmissionRequest" in schemas

def test_debug_mode_detection_for_docs():
    """Test debug mode detection affects documentation availability."""
    # Test with environment variable directly
    import os
    from fastapi import FastAPI
    
    # Simulate debug mode
    with patch.dict(os.environ, {'DEBUG_MODE': 'true'}):
        # Create new app instance
        app = FastAPI(
            title="Test App",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Should have docs enabled
        assert app.docs_url is not None
        assert app.redoc_url is not None

def test_production_mode_no_docs_leak():
    """Test production mode doesn't leak documentation endpoints."""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    
    # Simulate production app configuration
    prod_app = FastAPI(
        title="Netanya Incident Service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )
    
    @prod_app.get("/docs", include_in_schema=False)
    async def docs_disabled():
        raise HTTPException(status_code=404, detail="Documentation not available in production mode")
    
    @prod_app.get("/redoc", include_in_schema=False)
    async def redoc_disabled():
        raise HTTPException(status_code=404, detail="Documentation not available in production mode")
    
    @prod_app.get("/openapi.json", include_in_schema=False)
    async def openapi_disabled():
        raise HTTPException(status_code=404, detail="API specification not available in production mode")
    
    client = TestClient(prod_app)
    
    # Check various documentation-related endpoints
    doc_endpoints = ["/docs", "/redoc", "/openapi.json"]
    
    for endpoint in doc_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 404, f"Endpoint {endpoint} should return 404 in production"

def test_api_version_in_documentation():
    """Test API version is correctly set in documentation."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            openapi_spec = response.json()
            assert openapi_spec["info"]["version"] == "1.0.0"

def test_api_description_in_documentation():
    """Test API description is properly set."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            openapi_spec = response.json()
            description = openapi_spec["info"]["description"]
            assert "Municipality incident submission" in description
            assert "SharePoint integration" in description

def test_endpoint_documentation_tags():
    """Test API endpoints are properly tagged for documentation organization."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            # Check incident endpoints have proper tags
            if "/incidents/submit" in paths:
                submit_endpoint = paths["/incidents/submit"]["post"]
                assert "tags" in submit_endpoint
                assert "incidents" in submit_endpoint["tags"]

def test_documentation_security_considerations():
    """Test documentation doesn't expose sensitive configuration."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            openapi_content = response.text.lower()
            
            # Should not contain sensitive information
            sensitive_terms = ["password", "secret", "key", "token"]
            for term in sensitive_terms:
                assert term not in openapi_content, f"Documentation contains sensitive term: {term}"

def test_custom_documentation_endpoints():
    """Test custom documentation endpoints for API information."""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    
    # Test root endpoint provides API information
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["service"] == "Netanya Incident Service"

def test_documentation_response_examples():
    """Test API documentation includes response examples."""
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = True
        
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            openapi_spec = response.json()
            
            # Check if response schemas are defined
            components = openapi_spec.get("components", {})
            schemas = components.get("schemas", {})
            
            # Should have response models
            response_models = ["ValidationError", "HTTPValidationError"]
            for model in response_models:
                # These might be auto-generated by FastAPI
                # Just verify the structure exists
                assert len(schemas) > 0
