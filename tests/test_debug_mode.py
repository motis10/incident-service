"""
Test debug mode with mock response generation.
"""
import pytest
import re
from unittest.mock import patch
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_mock_service_import():
    """Test that mock service can be imported."""
    try:
        from app.services.mock_service import (
            MockSharePointService, MockTicketGenerator, MockResponse
        )
        assert MockSharePointService is not None
        assert MockTicketGenerator is not None
        assert MockResponse is not None
    except ImportError:
        pytest.fail("Could not import mock service")

def test_mock_ticket_generator():
    """Test mock ticket ID generation with timestamp."""
    from app.services.mock_service import MockTicketGenerator
    
    generator = MockTicketGenerator()
    
    # Generate multiple tickets
    tickets = [generator.generate_ticket_id() for _ in range(10)]
    
    # All should be unique
    assert len(set(tickets)) == 10
    
    # All should follow the pattern: NETANYA-YYYY-NNNNNN
    pattern = r'^NETANYA-\d{4}-\d{6}$'
    for ticket in tickets:
        assert re.match(pattern, ticket), f"Ticket {ticket} doesn't match pattern"
    
    # Should contain current year
    import datetime
    current_year = datetime.datetime.now().year
    for ticket in tickets:
        assert str(current_year) in ticket

def test_mock_response_structure():
    """Test mock response follows SharePoint format."""
    from app.services.mock_service import MockResponse
    
    response = MockResponse(
        result_code=200,
        error_description="",
        result_status="SUCCESS CREATE",
        data="NETANYA-2025-123456"
    )
    
    # Should match SharePoint API format
    assert response.result_code == 200
    assert response.error_description == ""
    assert response.result_status == "SUCCESS CREATE"
    assert response.data == "NETANYA-2025-123456"
    
    # Should be serializable to dict
    response_dict = response.to_dict()
    expected_keys = {"ResultCode", "ErrorDescription", "ResultStatus", "data"}
    assert set(response_dict.keys()) == expected_keys

def test_mock_sharepoint_service_initialization():
    """Test mock SharePoint service initialization."""
    from app.services.mock_service import MockSharePointService
    
    service = MockSharePointService()
    
    # Should have ticket generator
    assert service.ticket_generator is not None
    
    # Should be configurable for different response types
    assert hasattr(service, 'simulate_success')
    assert hasattr(service, 'simulate_error')

def test_mock_successful_submission():
    """Test mock successful incident submission."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    
    service = MockSharePointService()
    
    # Create test payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Mock test incident",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="123",
        callerFirstName="Mock",
        callerLastName="User",
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="mock@example.com",
        contactUsType="3"
    )
    
    # Submit to mock service
    response = service.submit_incident(payload)
    
    # Should return successful response
    assert response.result_code == 200
    assert response.result_status == "SUCCESS CREATE"
    assert response.error_description == ""
    assert response.data.startswith("NETANYA-")
    
    # Ticket should be well-formed
    assert re.match(r'^NETANYA-\d{4}-\d{6}$', response.data)

def test_mock_error_simulation():
    """Test mock error response simulation."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    
    service = MockSharePointService()
    
    # Configure for error simulation
    service.simulate_error("Invalid data format", 400)
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Error test incident",
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
    
    response = service.submit_incident(payload)
    
    # Should return error response
    assert response.result_code == 400
    assert response.result_status == "ERROR"
    assert response.error_description == "Invalid data format"
    assert response.data == ""

def test_mock_service_with_file():
    """Test mock service handles file attachments."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    from app.services.file_validation import MultipartFile
    
    service = MockSharePointService()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Mock test with file",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="456",
        callerFirstName="File",
        callerLastName="Test",
        callerTZ="987654321",
        callerPhone1="0507654321",
        callerEmail="file@example.com",
        contactUsType="3"
    )
    
    # Create mock file
    mock_file = MultipartFile(
        field_name="attachment",
        filename="mock_test.jpg",
        content_type="image/jpeg",
        data=b"mock_file_data"
    )
    
    # Submit with file
    response = service.submit_incident(payload, file=mock_file)
    
    # Should succeed and include file in metadata
    assert response.result_code == 200
    assert response.result_status == "SUCCESS CREATE"

def test_debug_mode_integration():
    """Test debug mode integration with incident service."""
    from app.services.incident_service import IncidentService
    from app.services.mock_service import MockSharePointService
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    # Create incident service with mock SharePoint client
    mock_client = MockSharePointService()
    service = IncidentService(sharepoint_client=mock_client)
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Debug",
            last_name="Test",
            phone="0501111111"
        ),
        category=Category(
            id=1,
            name="Debug Test",
            text="Debug mode test",
            image_url="https://example.com/debug.jpg",
            event_call_desc="Debug mode test"
        ),
        street=StreetNumber(
            id=1,
            name="Debug Street",
            image_url="https://example.com/debug_street.jpg",
            house_number="DEBUG"
        ),
        custom_text="Debug mode test incident"
    )
    
    # Submit incident in debug mode
    result = service.submit_incident(request)
    
    # Should succeed with mock ticket
    assert result.success is True
    assert result.ticket_id.startswith("NETANYA-")
    assert re.match(r'^NETANYA-\d{4}-\d{6}$', result.ticket_id)

def test_debug_logging_integration():
    """Test debug mode logging integration."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    from unittest.mock import patch
    
    service = MockSharePointService()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Debug logging test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="LOG",
        callerFirstName="Debug",
        callerLastName="Log",
        callerTZ="111111111",
        callerPhone1="0501111111",
        callerEmail="debug@example.com",
        contactUsType="3"
    )
    
    # Capture log messages
    with patch('app.services.mock_service.logger') as mock_logger:
        response = service.submit_incident(payload)
        
        # Should have logged debug information
        mock_logger.info.assert_called()
        
        # Log should contain relevant information
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        debug_logged = any("debug" in call.lower() or "mock" in call.lower() for call in log_calls)
        assert debug_logged

def test_mock_response_consistency():
    """Test that mock responses are consistent across calls."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    
    service = MockSharePointService()
    
    # Create identical payloads
    payload1 = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Consistency test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="CONS1",
        callerFirstName="Consistent",
        callerLastName="Test",
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="consistent@example.com",
        contactUsType="3"
    )
    
    payload2 = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Consistency test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="CONS2",
        callerFirstName="Consistent",
        callerLastName="Test",
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="consistent@example.com",
        contactUsType="3"
    )
    
    # Submit both
    response1 = service.submit_incident(payload1)
    response2 = service.submit_incident(payload2)
    
    # Both should succeed with different ticket IDs
    assert response1.result_code == 200
    assert response2.result_code == 200
    assert response1.data != response2.data  # Different tickets
    assert response1.result_status == response2.result_status  # Same status

def test_mock_ticket_generation_with_timestamp():
    """Test mock ticket generation includes timestamp information."""
    from app.services.mock_service import MockTicketGenerator
    import time
    
    generator = MockTicketGenerator()
    
    # Generate tickets at different times
    ticket1 = generator.generate_ticket_id()
    time.sleep(0.01)  # Small delay
    ticket2 = generator.generate_ticket_id()
    
    # Should be different (timestamp-based)
    assert ticket1 != ticket2
    
    # Both should contain current year
    import datetime
    current_year = str(datetime.datetime.now().year)
    assert current_year in ticket1
    assert current_year in ticket2

def test_mock_error_types():
    """Test different types of mock errors."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    
    service = MockSharePointService()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Error type test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="ERR",
        callerFirstName="Error",
        callerLastName="Types",
        callerTZ="999999999",
        callerPhone1="0509999999",
        callerEmail="error@example.com",
        contactUsType="3"
    )
    
    # Test different error scenarios
    error_scenarios = [
        (400, "Invalid data format"),
        (500, "Internal server error"),
        (422, "Validation failed"),
        (413, "File too large")
    ]
    
    for error_code, error_message in error_scenarios:
        service.simulate_error(error_message, error_code)
        response = service.submit_incident(payload)
        
        assert response.result_code == error_code
        assert response.error_description == error_message
        assert response.result_status == "ERROR"
        assert response.data == ""

def test_no_external_calls_in_debug_mode():
    """Test that debug mode never makes external calls."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    import requests
    from unittest.mock import patch
    
    service = MockSharePointService()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="No external calls test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="NOEXT",
        callerFirstName="NoExternal",
        callerLastName="Calls",
        callerTZ="000000000",
        callerPhone1="0500000000",
        callerEmail="noext@example.com",
        contactUsType="3"
    )
    
    # Patch requests to ensure no external calls
    with patch.object(requests, 'post') as mock_post:
        response = service.submit_incident(payload)
        
        # Should succeed without external calls
        assert response.result_code == 200
        assert mock_post.call_count == 0  # No external requests made

def test_mock_service_reset():
    """Test mock service can reset to default behavior."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    
    service = MockSharePointService()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Reset test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="RESET",
        callerFirstName="Reset",
        callerLastName="Test",
        callerTZ="555555555",
        callerPhone1="0505555555",
        callerEmail="reset@example.com",
        contactUsType="3"
    )
    
    # Set error mode
    service.simulate_error("Test error", 400)
    response1 = service.submit_incident(payload)
    assert response1.result_code == 400
    
    # Reset to success mode
    service.simulate_success()
    response2 = service.submit_incident(payload)
    assert response2.result_code == 200
