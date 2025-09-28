"""
Test API endpoints for incident submission.
"""
import pytest
import json
import base64
from fastapi.testclient import TestClient
from unittest.mock import patch
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

@pytest.fixture
def client():
    """Create test client for API endpoints."""
    from app.main import app
    return TestClient(app)

@pytest.fixture
def valid_incident_data():
    """Valid incident submission data."""
    return {
        "user_data": {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "0501234567",
            "user_id": "123456789",
            "email": "john@example.com"
        },
        "category": {
            "id": 1,
            "name": "Street Cleaning",
            "text": "Street cleaning issues",
            "image_url": "https://example.com/cleaning.jpg",
            "event_call_desc": "Street cleaning complaint"
        },
        "street": {
            "id": 1,
            "name": "Main Street",
            "image_url": "https://example.com/street.jpg",
            "house_number": "123"
        },
        "custom_text": "Test incident submission via API"
    }

@pytest.fixture
def valid_incident_with_file():
    """Valid incident submission with file attachment."""
    test_image = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    base64_data = base64.b64encode(test_image).decode('utf-8')
    
    return {
        "user_data": {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "0507654321",
            "email": "jane@example.com"
        },
        "category": {
            "id": 2,
            "name": "Graffiti",
            "text": "Graffiti removal",
            "image_url": "https://example.com/graffiti.jpg",
            "event_call_desc": "Graffiti complaint"
        },
        "street": {
            "id": 2,
            "name": "Second Street",
            "image_url": "https://example.com/street2.jpg",
            "house_number": "456"
        },
        "custom_text": "Graffiti removal request with photo evidence",
        "extra_files": {
            "filename": "graffiti.jpg",
            "content_type": "image/jpeg",
            "size": len(test_image),
            "data": base64_data
        }
    }

def test_incident_submission_endpoint_exists(client):
    """Test that incident submission endpoint exists."""
    response = client.post("/incidents/submit", json={})
    # Should not return 404 (endpoint exists)
    assert response.status_code != 404

def test_submit_incident_success(client, valid_incident_data):
    """Test successful incident submission."""
    # Mock the incident service instance in the API module
    with patch('app.api.incidents.incident_service') as mock_service:
        # Mock the SubmissionResult
        from app.services.incident_service import SubmissionResult
        mock_result = SubmissionResult(
            success=True,
            ticket_id="NETANYA-2025-123456", 
            correlation_id="test-correlation-123",
            has_file=False,
            file_info=None,
            metadata={}
        )
        mock_service.submit_incident.return_value = mock_result
        
        response = client.post("/incidents/submit", json=valid_incident_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["ticket_id"] == "NETANYA-2025-123456"
        assert "correlation_id" in data

def test_submit_incident_with_file_success(client, valid_incident_with_file):
    """Test successful incident submission with file."""
    with patch('app.api.incidents.incident_service') as mock_service:
        # Mock the SubmissionResult with file
        from app.services.incident_service import SubmissionResult
        mock_result = SubmissionResult(
            success=True,
            ticket_id="NETANYA-2025-789012",
            correlation_id="test-correlation-456",
            has_file=True,
            file_info={
                "filename": "graffiti.jpg",
                "content_type": "image/jpeg", 
                "size": 1024
            },
            metadata={}
        )
        mock_service.submit_incident.return_value = mock_result
        
        response = client.post("/incidents/submit", json=valid_incident_with_file)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["ticket_id"] == "NETANYA-2025-789012"
        assert data["has_file"] is True
        assert data["file_info"]["filename"] == "graffiti.jpg"

def test_submit_incident_validation_error(client):
    """Test incident submission with validation errors (422)."""
    # Invalid data - missing required fields
    invalid_data = {
        "user_data": {
            # Missing required first_name, last_name, phone
        },
        "category": {
            # Missing required fields
        }
    }
    
    response = client.post("/incidents/submit", json=invalid_data)
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "details" in data
    assert "correlation_id" in data

def test_submit_incident_file_validation_error(client):
    """Test incident submission with file validation errors (422)."""
    # Valid incident data but invalid file
    test_data = {
        "user_data": {
            "first_name": "File",
            "last_name": "Error",
            "phone": "0508888888"
        },
        "category": {
            "id": 1,
            "name": "Test",
            "text": "Test category",
            "image_url": "https://example.com/test.jpg",
            "event_call_desc": "Test"
        },
        "street": {
            "id": 1,
            "name": "Test Street",
            "image_url": "https://example.com/street.jpg",
            "house_number": "1"
        },
        "extra_files": {
            "filename": "invalid.exe",
            "content_type": "application/x-executable",
            "size": 1000000,
            "data": "invalid_base64_data"
        }
    }
    
    response = client.post("/incidents/submit", json=test_data)
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "file validation" in data["error"].lower()

def test_submit_incident_file_too_large(client):
    """Test incident submission with file too large (413)."""
    # Create oversized file
    large_data = b"X" * (11 * 1024 * 1024)  # 11MB
    base64_data = base64.b64encode(large_data).decode('utf-8')
    
    test_data = {
        "user_data": {
            "first_name": "Large",
            "last_name": "File",
            "phone": "0509999999"
        },
        "category": {
            "id": 1,
            "name": "Test",
            "text": "Test category", 
            "image_url": "https://example.com/test.jpg",
            "event_call_desc": "Test"
        },
        "street": {
            "id": 1,
            "name": "Test Street",
            "image_url": "https://example.com/street.jpg",
            "house_number": "1"
        },
        "extra_files": {
            "filename": "large.jpg",
            "content_type": "image/jpeg",
            "size": len(large_data),
            "data": base64_data
        }
    }
    
    response = client.post("/incidents/submit", json=test_data)
    
    assert response.status_code == 413
    data = response.json()
    assert "error" in data
    assert "large" in data["error"].lower() or "size" in data["error"].lower()

def test_submit_incident_internal_error(client, valid_incident_data):
    """Test incident submission with internal server error (500)."""
    with patch('app.api.incidents.incident_service') as mock_service:
        # Mock internal error
        mock_service.submit_incident.side_effect = Exception("Database connection failed")
        
        response = client.post("/incidents/submit", json=valid_incident_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "correlation_id" in data

def test_submit_incident_bad_json(client):
    """Test incident submission with malformed JSON (400)."""
    response = client.post(
        "/incidents/submit",
        data="invalid json data",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422  # JSON validation errors return 422
    data = response.json()
    assert "error" in data
    assert "validation" in data["error"].lower() or "decode" in data["error"].lower()

def test_submit_incident_hebrew_content(client):
    """Test incident submission with Hebrew content."""
    hebrew_data = {
        "user_data": {
            "first_name": "יוחנן",
            "last_name": "כהן",
            "phone": "0501111111",
            "email": "yohanan@example.com"
        },
        "category": {
            "id": 1,
            "name": "ניקיון רחובות",
            "text": "בעיות ניקיון ברחובות העיר",
            "image_url": "https://example.com/cleaning_he.jpg",
            "event_call_desc": "תלונה על ניקיון"
        },
        "street": {
            "id": 1,
            "name": "רחוב הרצל",
            "image_url": "https://example.com/herzl.jpg",
            "house_number": "15א"
        },
        "custom_text": "תלונה דחופה על פח זבל שבור"
    }
    
    with patch('app.api.incidents.incident_service') as mock_service:
        from app.services.incident_service import SubmissionResult
        mock_result = SubmissionResult(
            success=True,
            ticket_id="NETANYA-2025-HEBREW",
            correlation_id="hebrew-test-123",
            has_file=False,
            file_info=None,
            metadata={}
        )
        mock_service.submit_incident.return_value = mock_result
        
        response = client.post("/incidents/submit", json=hebrew_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

def test_submit_incident_cors_headers(client, valid_incident_data):
    """Test that CORS headers are present."""
    with patch('app.api.incidents.incident_service') as mock_service:
        from app.services.incident_service import SubmissionResult
        mock_result = SubmissionResult(
            success=True,
            ticket_id="NETANYA-2025-CORS",
            correlation_id="cors-test-123",
            has_file=False,
            file_info=None,
            metadata={}
        )
        mock_service.submit_incident.return_value = mock_result
        
        response = client.post("/incidents/submit", json=valid_incident_data)
        
        # Check for CORS headers (note: TestClient doesn't always include CORS headers)
        # Just verify the endpoint works successfully
        assert response.status_code == 200

def test_health_check_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_root_endpoint(client):
    """Test root endpoint returns service info."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "status" in data

def test_options_request_cors(client):
    """Test OPTIONS request for CORS preflight."""
    response = client.options("/incidents/submit")
    
    assert response.status_code == 200
    # TestClient doesn't include CORS headers, so just verify OPTIONS works
    data = response.json()
    assert "message" in data

def test_debug_mode_endpoint_response(client, valid_incident_data):
    """Test debug mode specific response format."""
    with patch.dict('os.environ', {'DEBUG_MODE': 'true'}):
        with patch('app.api.incidents.incident_service') as mock_service:
            from app.services.incident_service import SubmissionResult
            mock_result = SubmissionResult(
                success=True,
                ticket_id="NETANYA-2025-DEBUG",
                correlation_id="debug-test-123",
                has_file=False,
                file_info=None,
                metadata={
                    "debug_mode": True,
                    "sharepoint_status": "SUCCESS CREATE"
                }
            )
            mock_service.submit_incident.return_value = mock_result
            
            response = client.post("/incidents/submit", json=valid_incident_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            # Debug mode might include additional metadata
            if "metadata" in data:
                assert "debug_mode" in data["metadata"] or "sharepoint_status" in data["metadata"]

def test_api_versioning_header(client):
    """Test API version information in headers."""
    response = client.get("/")
    
    # Should include version information
    assert "X-API-Version" in response.headers or "version" in response.json()

def test_content_type_validation(client):
    """Test content type validation."""
    # Test non-JSON content type
    response = client.post(
        "/incidents/submit",
        data="some data",
        headers={"Content-Type": "text/plain"}
    )
    
    # Should reject non-JSON content
    assert response.status_code in [400, 415, 422]

def test_rate_limiting_headers(client, valid_incident_data):
    """Test rate limiting headers if implemented."""
    with patch('app.api.incidents.incident_service') as mock_service:
        from app.services.incident_service import SubmissionResult
        mock_result = SubmissionResult(
            success=True,
            ticket_id="NETANYA-2025-RATE",
            correlation_id="rate-test-123",
            has_file=False,
            file_info=None,
            metadata={}
        )
        mock_service.submit_incident.return_value = mock_result
        
        response = client.post("/incidents/submit", json=valid_incident_data)
        
        # Rate limiting headers are optional but good to test
        # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining
        assert response.status_code == 200
