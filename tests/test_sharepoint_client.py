"""
Test SharePoint client for NetanyaMuni API communication.
"""
import pytest
import json
from unittest.mock import patch, Mock
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_sharepoint_client_import():
    """Test that SharePoint client can be imported."""
    try:
        from app.clients.sharepoint import (
            SharePointClient, SharePointError, SharePointResponse,
            MultipartRequest
        )
        assert SharePointClient is not None
        assert SharePointError is not None
        assert SharePointResponse is not None
        assert MultipartRequest is not None
    except ImportError:
        pytest.fail("Could not import SharePoint client")

def test_sharepoint_client_initialization():
    """Test SharePoint client initialization."""
    from app.clients.sharepoint import SharePointClient
    
    # Test with default endpoint
    client = SharePointClient()
    assert client is not None
    
    # Test with custom endpoint
    custom_endpoint = "https://custom.sharepoint.com/incidents.ashx"
    client_custom = SharePointClient(endpoint_url=custom_endpoint)
    assert client_custom.endpoint_url == custom_endpoint

def test_required_headers_configuration():
    """Test required NetanyaMuni headers are configured."""
    from app.clients.sharepoint import SharePointClient
    
    client = SharePointClient()
    headers = client.get_required_headers()
    
    # Check required municipality headers
    assert headers["Origin"] == "https://www.netanya.muni.il"
    assert "PublicComplaints.aspx" in headers["Referer"]
    assert headers["X-Requested-With"] == "XMLHttpRequest"
    assert "multipart/form-data" in headers["Content-Type"]

def test_webkit_boundary_generation():
    """Test WebKit boundary format generation."""
    from app.clients.sharepoint import SharePointClient
    
    client = SharePointClient()
    boundary = client.generate_webkit_boundary()
    
    # Should be WebKit-style boundary
    assert boundary.startswith("----WebKitFormBoundary")
    assert len(boundary) == 38  # WebKit boundary length
    
    # Should be unique
    boundary2 = client.generate_webkit_boundary()
    assert boundary != boundary2

def test_multipart_request_construction():
    """Test multipart request construction for SharePoint."""
    from app.clients.sharepoint import SharePointClient
    from app.models.sharepoint import APIPayload
    
    client = SharePointClient()
    
    # Create test payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Test complaint",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="123",
        callerFirstName="John",
        callerLastName="Doe",
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="john@example.com",
        contactUsType="3"
    )
    
    multipart_request = client.build_multipart_request(payload)
    
    assert multipart_request.boundary is not None
    assert multipart_request.body is not None
    assert multipart_request.content_type.startswith("multipart/form-data")
    
    # Should contain JSON field with payload
    body_str = multipart_request.body.decode('utf-8')
    assert 'name="json"' in body_str
    assert "Test complaint" in body_str

def test_multipart_request_with_file():
    """Test multipart request construction with file attachment."""
    from app.clients.sharepoint import SharePointClient
    from app.models.sharepoint import APIPayload
    from app.services.file_validation import MultipartFile
    
    client = SharePointClient()
    
    # Create test payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Test with image",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="123",
        callerFirstName="Jane",
        callerLastName="Smith",
        callerTZ="987654321",
        callerPhone1="0507654321",
        callerEmail="jane@example.com",
        contactUsType="3"
    )
    
    # Create test file
    test_file = MultipartFile(
        field_name="attachment",
        filename="evidence.jpg",
        content_type="image/jpeg",
        data=b"fake_jpeg_data_for_testing"
    )
    
    multipart_request = client.build_multipart_request(payload, file=test_file)
    
    # Should contain both JSON and file
    body_str = multipart_request.body.decode('utf-8')
    assert 'name="json"' in body_str
    assert 'name="attachment"' in body_str
    assert 'filename="evidence.jpg"' in body_str
    assert "fake_jpeg_data_for_testing" in body_str

def test_sharepoint_response_parsing():
    """Test SharePoint API response parsing."""
    from app.clients.sharepoint import SharePointClient
    from app.models.response import APIResponse
    
    client = SharePointClient()
    
    # Test successful response
    success_response_json = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "TICKET-12345"
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = success_response_json
    mock_response.text = json.dumps(success_response_json)
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = mock_response.text.encode('utf-8')
    mock_response.encoding = "utf-8"
    
    parsed_response = client.parse_sharepoint_response(mock_response)
    
    assert isinstance(parsed_response, APIResponse)
    assert parsed_response.ResultCode == 200
    assert parsed_response.ResultStatus == "SUCCESS CREATE"
    assert parsed_response.data == "TICKET-12345"

def test_sharepoint_error_response_parsing():
    """Test SharePoint error response parsing."""
    from app.clients.sharepoint import SharePointClient, SharePointError
    
    client = SharePointClient()
    
    # Test error response
    error_response_json = {
        "ResultCode": 400,
        "ErrorDescription": "Invalid data provided",
        "ResultStatus": "ERROR",
        "data": ""
    }
    
    mock_response = Mock()
    mock_response.status_code = 200  # SharePoint returns 200 even for errors
    mock_response.json.return_value = error_response_json
    mock_response.text = json.dumps(error_response_json)
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = mock_response.text.encode('utf-8')
    mock_response.encoding = "utf-8"
    
    with pytest.raises(SharePointError) as exc_info:
        client.parse_sharepoint_response(mock_response)
    
    assert "Invalid data provided" in str(exc_info.value)

def test_submit_to_sharepoint_success():
    """Test successful submission to SharePoint."""
    from app.clients.sharepoint import SharePointClient
    from app.models.sharepoint import APIPayload
    from app.models.response import APIResponse
    
    client = SharePointClient()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Integration test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="456",
        callerFirstName="Test",
        callerLastName="User",
        callerTZ="111111111",
        callerPhone1="0501111111",
        callerEmail="test@example.com",
        contactUsType="3"
    )
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "TICKET-67890"
    }
    mock_response.text = json.dumps(mock_response.json.return_value)
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = mock_response.text.encode('utf-8')
    mock_response.encoding = "utf-8"
    
    with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
        result = client.submit_to_sharepoint(payload)
        
        # Check request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check endpoint
        assert client.endpoint_url in call_args[0][0]
        
        # Check headers
        headers = call_args[1]["headers"]
        assert headers["Origin"] == "https://www.netanya.muni.il"
        assert headers["X-Requested-With"] == "XMLHttpRequest"
        
        # Check result
        assert isinstance(result, APIResponse)
        assert result.ResultCode == 200
        assert result.data == "TICKET-67890"

def test_submit_to_sharepoint_with_file():
    """Test submission to SharePoint with file attachment."""
    from app.clients.sharepoint import SharePointClient
    from app.models.sharepoint import APIPayload
    from app.services.file_validation import MultipartFile
    
    client = SharePointClient()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Test with file",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="789",
        callerFirstName="File",
        callerLastName="Tester",
        callerTZ="222222222",
        callerPhone1="0502222222",
        callerEmail="file@example.com",
        contactUsType="3"
    )
    
    test_file = MultipartFile(
        field_name="attachment",
        filename="test_image.png",
        content_type="image/png",
        data=b"fake_png_data"
    )
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "TICKET-FILE-123"
    }
    mock_response.text = json.dumps(mock_response.json.return_value)
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = mock_response.text.encode('utf-8')
    mock_response.encoding = "utf-8"
    
    with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
        result = client.submit_to_sharepoint(payload, file=test_file)
        
        # Check request was made
        mock_post.assert_called_once()
        
        # Check result includes file processing
        assert result.data == "TICKET-FILE-123"

def test_timeout_and_retry_configuration():
    """Test timeout and retry configuration."""
    from app.clients.sharepoint import SharePointClient
    
    # Test with custom timeout
    client = SharePointClient(timeout=30)
    assert client.timeout == 30
    
    # Test with custom retry attempts
    client_retry = SharePointClient(max_retries=5)
    assert client_retry.max_retries == 5

def test_network_error_handling():
    """Test network error handling and retries."""
    from app.clients.sharepoint import SharePointClient, SharePointError
    from app.models.sharepoint import APIPayload
    import requests
    
    client = SharePointClient(max_retries=2)
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400", 
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Network test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="999",
        callerFirstName="Network",
        callerLastName="Error",
        callerTZ="333333333",
        callerPhone1="0503333333",
        callerEmail="network@example.com",
        contactUsType="3"
    )
    
    # Mock network error
    with patch.object(client.session, 'post', side_effect=requests.ConnectionError("Network error")):
        with pytest.raises(SharePointError) as exc_info:
            client.submit_to_sharepoint(payload)
        
        assert "Network error" in str(exc_info.value)

def test_http_error_handling():
    """Test HTTP error response handling."""
    from app.clients.sharepoint import SharePointClient, SharePointError
    from app.models.sharepoint import APIPayload
    
    client = SharePointClient()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה", 
        eventCallCenterId="3",
        eventCallDesc="HTTP error test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="500",
        callerFirstName="HTTP",
        callerLastName="Error",
        callerTZ="444444444",
        callerPhone1="0504444444",
        callerEmail="http@example.com",
        contactUsType="3"
    )
    
    # Mock HTTP 500 error
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.content = mock_response.text.encode('utf-8')
    mock_response.json.side_effect = ValueError("No JSON")
    
    with patch.object(client.session, 'post', return_value=mock_response):
        with pytest.raises(SharePointError) as exc_info:
            client.submit_to_sharepoint(payload)
        
        assert "500" in str(exc_info.value)

def test_json_parsing_error_handling():
    """Test JSON parsing error handling."""
    from app.clients.sharepoint import SharePointClient, SharePointError
    from app.models.sharepoint import APIPayload
    
    client = SharePointClient()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3", 
        eventCallDesc="JSON error test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="400",
        callerFirstName="JSON",
        callerLastName="Error",
        callerTZ="555555555",
        callerPhone1="0505555555",
        callerEmail="json@example.com",
        contactUsType="3"
    )
    
    # Mock response with invalid JSON
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "Invalid JSON response"
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    with patch.object(client.session, 'post', return_value=mock_response):
        with pytest.raises(SharePointError) as exc_info:
            client.submit_to_sharepoint(payload)
        
        assert "JSON" in str(exc_info.value) or "parse" in str(exc_info.value)

def test_unicode_handling_in_requests():
    """Test Unicode handling in SharePoint requests."""
    from app.clients.sharepoint import SharePointClient
    from app.models.sharepoint import APIPayload
    
    client = SharePointClient()
    
    # Test with Hebrew text
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="תלונה על זבל ברחוב הרצל",  # Hebrew complaint
        streetCode="898", 
        streetDesc="קרל פופר",
        houseNumber="15א",  # Hebrew house number
        callerFirstName="יוחנן",  # Hebrew name
        callerLastName="כהן",
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="yohanan@example.com",
        contactUsType="3"
    )
    
    # Build multipart request
    multipart_request = client.build_multipart_request(payload)
    
    # Should handle Unicode properly
    body_str = multipart_request.body.decode('utf-8')
    assert "תלונה על זבל" in body_str
    assert "יוחנן" in body_str
    assert "נתניה" in body_str

def test_sharepoint_response_model():
    """Test SharePoint response model structure."""
    from app.clients.sharepoint import SharePointResponse
    
    response = SharePointResponse(
        success=True,
        result_code=200,
        error_description="",
        result_status="SUCCESS CREATE",
        data="TICKET-TEST",
        raw_response={"test": "data"}
    )
    
    assert response.success is True
    assert response.result_code == 200
    assert response.data == "TICKET-TEST"
    assert response.raw_response["test"] == "data"
