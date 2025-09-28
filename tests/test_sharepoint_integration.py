"""
Integration tests for SharePoint client with complete service workflows.
"""
import pytest
import base64
from unittest.mock import patch, Mock
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_complete_incident_submission_workflow():
    """Test complete workflow from request models to SharePoint submission."""
    from app.clients.sharepoint import SharePointClient
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    from app.models.sharepoint import APIPayload
    from app.services.file_validation import FileValidationService
    
    # Create complete incident submission
    user_data = UserData(
        first_name="Integration",
        last_name="Test",
        phone="0501234567",
        user_id="123456789",
        email="integration@example.com"
    )
    
    category = Category(
        id=1,
        name="Street Cleaning",
        text="Street cleaning issues",
        image_url="https://example.com/street_cleaning.jpg",
        event_call_desc="Street cleaning complaint"
    )
    
    street = StreetNumber(
        id=1,
        name="Integration Street",
        image_url="https://example.com/street.jpg",
        house_number="42"
    )
    
    # Add file attachment
    test_image_data = b"fake_jpeg_header_data"
    base64_data = base64.b64encode(test_image_data).decode('utf-8')
    
    image_file = ImageFile(
        filename="evidence.jpg",
        content_type="image/jpeg",
        size=len(test_image_data),
        data=base64_data
    )
    
    request = IncidentSubmissionRequest(
        user_data=user_data,
        category=category,
        street=street,
        custom_text="Integration test incident with file attachment",
        extra_files=image_file
    )
    
    # Validate file
    file_service = FileValidationService()
    file_validation = file_service.validate_file(image_file)
    assert file_validation.is_valid
    
    # Prepare multipart file
    multipart_file = file_service.prepare_multipart_file(image_file)
    
    # Transform to SharePoint payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc=request.custom_text or request.category.event_call_desc,
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber=request.street.house_number,
        callerFirstName=request.user_data.first_name,
        callerLastName=request.user_data.last_name,
        callerTZ=request.user_data.user_id or "",
        callerPhone1=request.user_data.phone,
        callerEmail=request.user_data.email or "",
        contactUsType="3"
    )
    
    # Submit to SharePoint
    client = SharePointClient()
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "INTEGRATION-TICKET-123"
    }
    
    with patch.object(client.session, 'post', return_value=mock_response):
        result = client.submit_to_sharepoint(payload, file=multipart_file)
        
        assert result.ResultCode == 200
        assert result.data == "INTEGRATION-TICKET-123"
        assert result.ResultStatus == "SUCCESS CREATE"

def test_payload_transformation_accuracy():
    """Test accurate transformation from request models to SharePoint payload."""
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    from app.models.sharepoint import APIPayload
    
    # Create test data with Hebrew text
    user_data = UserData(
        first_name="יוחנן",
        last_name="כהן",
        phone="0507654321",
        user_id="987654321",
        email="yohanan@example.com"
    )
    
    category = Category(
        id=2,
        name="ניקיון רחובות",
        text="בעיות ניקיון ברחובות העיר",
        image_url="https://example.com/cleaning.jpg",
        event_call_desc="תלונה על ניקיון רחובות"
    )
    
    street = StreetNumber(
        id=2,
        name="רחוב הרצל",
        image_url="https://example.com/herzl.jpg",
        house_number="15א"
    )
    
    request = IncidentSubmissionRequest(
        user_data=user_data,
        category=category,
        street=street,
        custom_text="תלונה חמורה על זבל ברחוב"
    )
    
    # Transform to SharePoint format
    payload = APIPayload(
        eventCallSourceId=4,  # Fixed value
        cityCode="7400",      # Fixed value
        cityDesc="נתניה",     # Fixed value
        eventCallCenterId="3", # Fixed value
        eventCallDesc=request.custom_text,  # Custom text takes priority
        streetCode="898",     # Fixed value
        streetDesc="קרל פופר", # Fixed value
        houseNumber=request.street.house_number,
        callerFirstName=request.user_data.first_name,
        callerLastName=request.user_data.last_name,
        callerTZ=request.user_data.user_id,
        callerPhone1=request.user_data.phone,
        callerEmail=request.user_data.email,
        contactUsType="3"     # Fixed value
    )
    
    # Verify fixed municipality values
    assert payload.eventCallSourceId == 4
    assert payload.cityCode == "7400"
    assert payload.cityDesc == "נתניה"
    assert payload.eventCallCenterId == "3"
    assert payload.streetCode == "898"
    assert payload.streetDesc == "קרל פופר"
    assert payload.contactUsType == "3"
    
    # Verify dynamic values
    assert payload.eventCallDesc == "תלונה חמורה על זבל ברחוב"
    assert payload.houseNumber == "15א"
    assert payload.callerFirstName == "יוחנן"
    assert payload.callerLastName == "כהן"
    assert payload.callerPhone1 == "0507654321"

def test_multipart_request_with_hebrew_content():
    """Test multipart request generation with Hebrew content."""
    from app.clients.sharepoint import SharePointClient
    from app.models.sharepoint import APIPayload
    from app.services.file_validation import MultipartFile
    
    client = SharePointClient()
    
    # Create payload with Hebrew content
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="תלונה דחופה על פח זבל שבור בכניסה לבניין",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="23ב",
        callerFirstName="שרה",
        callerLastName="לוי",
        callerTZ="123456789",
        callerPhone1="0508765432",
        callerEmail="sarah.levy@example.com",
        contactUsType="3"
    )
    
    # Create Hebrew filename file
    hebrew_file = MultipartFile(
        field_name="attachment",
        filename="תמונת_ראיות_זבל.jpg",
        content_type="image/jpeg",
        data="תוכן קובץ דמה".encode('utf-8')
    )
    
    # Build multipart request
    multipart_request = client.build_multipart_request(payload, file=hebrew_file)
    
    # Verify UTF-8 encoding works correctly
    body_str = multipart_request.body.decode('utf-8')
    assert "תלונה דחופה" in body_str
    assert "שרה" in body_str
    assert "לוי" in body_str
    assert "תמונת_ראיות_זבל.jpg" in body_str
    assert "תוכן קובץ דמה" in body_str

def test_error_handling_integration():
    """Test error handling integration across all components."""
    from app.clients.sharepoint import SharePointClient, SharePointError
    from app.services.error_handling import ErrorHandlingService
    from app.models.sharepoint import APIPayload
    
    client = SharePointClient()
    error_service = ErrorHandlingService()
    
    # Create test payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Error handling test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="ERROR",
        callerFirstName="Error",
        callerLastName="Test",
        callerTZ="000000000",
        callerPhone1="0500000000",
        callerEmail="error@example.com",
        contactUsType="3"
    )
    
    # Mock SharePoint error response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 400,
        "ErrorDescription": "Invalid house number format",
        "ResultStatus": "ERROR",
        "data": ""
    }
    
    with patch.object(client.session, 'post', return_value=mock_response):
        try:
            client.submit_to_sharepoint(payload)
            pytest.fail("Should have raised SharePointError")
        except SharePointError as e:
            # Handle SharePoint error with error service
            error_response = error_service.create_500_response(
                message="SharePoint submission failed",
                error_details=str(e)
            )
            
            assert error_response["status_code"] == 500
            assert "correlation_id" in error_response
            assert "Invalid house number format" in error_response["details"]

def test_configuration_integration():
    """Test SharePoint client integration with configuration service."""
    from app.clients.sharepoint import SharePointClient
    from app.core.config import ConfigService
    
    # Test with custom endpoint from configuration
    config_service = ConfigService()
    
    # Create client with configuration endpoint
    custom_endpoint = "https://test.netanya.muni.il/incidents.ashx"
    client = SharePointClient(endpoint_url=custom_endpoint)
    
    assert client.endpoint_url == custom_endpoint
    
    # Verify headers are still correct
    headers = client.get_required_headers()
    assert headers["Origin"] == "https://www.netanya.muni.il"
    assert "PublicComplaints.aspx" in headers["Referer"]

def test_large_file_multipart_handling():
    """Test handling of larger file attachments in multipart requests."""
    from app.clients.sharepoint import SharePointClient
    from app.models.sharepoint import APIPayload
    from app.services.file_validation import MultipartFile
    
    client = SharePointClient()
    
    # Create payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Large file test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="100",
        callerFirstName="Large",
        callerLastName="File",
        callerTZ="111111111",
        callerPhone1="0501111111",
        callerEmail="large@example.com",
        contactUsType="3"
    )
    
    # Create larger file (1MB simulated)
    large_file_data = b"X" * (1024 * 1024)  # 1MB of data
    large_file = MultipartFile(
        field_name="attachment",
        filename="large_evidence.jpg",
        content_type="image/jpeg",
        data=large_file_data
    )
    
    # Build multipart request
    multipart_request = client.build_multipart_request(payload, file=large_file)
    
    # Verify request structure
    assert multipart_request.boundary is not None
    assert len(multipart_request.body) > 1024 * 1024  # Should include file data
    assert "large_evidence.jpg" in multipart_request.body.decode('utf-8', errors='ignore')

def test_concurrent_sharepoint_requests():
    """Test SharePoint client handling of concurrent requests."""
    from app.clients.sharepoint import SharePointClient
    from app.models.sharepoint import APIPayload
    import concurrent.futures
    
    def make_request(client, request_id):
        payload = APIPayload(
            eventCallSourceId=4,
            cityCode="7400",
            cityDesc="נתניה",
            eventCallCenterId="3",
            eventCallDesc=f"Concurrent test {request_id}",
            streetCode="898",
            streetDesc="קרל פופר",
            houseNumber=str(request_id),
            callerFirstName="Concurrent",
            callerLastName="Test",
            callerTZ="123456789",
            callerPhone1="0501234567",
            callerEmail="concurrent@example.com",
            contactUsType="3"
        )
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ResultCode": 200,
            "ErrorDescription": "",
            "ResultStatus": "SUCCESS CREATE",
            "data": f"CONCURRENT-{request_id}"
        }
        
        with patch.object(client.session, 'post', return_value=mock_response):
            return client.submit_to_sharepoint(payload)
    
    client = SharePointClient()
    
    # Test concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(make_request, client, i) 
            for i in range(10)
        ]
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # All should succeed
    assert len(results) == 10
    assert all(result.ResultCode == 200 for result in results)

def test_full_system_mock_integration():
    """Test full system integration with mock SharePoint service."""
    from app.clients.sharepoint import SharePointClient
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    from app.models.sharepoint import APIPayload
    from app.services.file_validation import FileValidationService
    from app.services.error_handling import ErrorHandlingService
    
    # Initialize all services
    sharepoint_client = SharePointClient()
    file_service = FileValidationService()
    error_service = ErrorHandlingService()
    
    # Create incident request
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="System",
            last_name="Integration",
            phone="0509876543",
            user_id="987654321",
            email="system@example.com"
        ),
        category=Category(
            id=1,
            name="System Test",
            text="System integration test",
            image_url="https://example.com/test.jpg",
            event_call_desc="System integration test category"
        ),
        street=StreetNumber(
            id=1,
            name="Integration Avenue",
            image_url="https://example.com/avenue.jpg",
            house_number="999"
        ),
        custom_text="Complete system integration test"
    )
    
    # Transform to SharePoint payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc=request.custom_text,
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber=request.street.house_number,
        callerFirstName=request.user_data.first_name,
        callerLastName=request.user_data.last_name,
        callerTZ=request.user_data.user_id,
        callerPhone1=request.user_data.phone,
        callerEmail=request.user_data.email,
        contactUsType="3"
    )
    
    # Mock successful SharePoint response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "SYSTEM-INTEGRATION-SUCCESS"
    }
    
    correlation_id = error_service.correlation_generator.generate()
    
    with patch.object(sharepoint_client.session, 'post', return_value=mock_response):
        result = sharepoint_client.submit_to_sharepoint(payload)
        
        # Verify successful integration
        assert result.ResultCode == 200
        assert result.data == "SYSTEM-INTEGRATION-SUCCESS"
        
        # Create success response structure
        success_response = {
            "success": True,
            "ticket_id": result.data,
            "correlation_id": correlation_id,
            "message": "Incident submitted successfully"
        }
        
        assert success_response["success"] is True
        assert success_response["ticket_id"] == "SYSTEM-INTEGRATION-SUCCESS"
