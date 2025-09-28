"""
Integration tests for debug mode with configuration system.
"""
import pytest
import os
from unittest.mock import patch
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_debug_mode_detection():
    """Test debug mode detection from configuration."""
    from app.core.config import ConfigService
    from app.services.mock_service import MockSharePointService
    from app.services.incident_service import IncidentService
    
    # Test debug mode enabled
    with patch.dict(os.environ, {'DEBUG_MODE': 'true'}):
        config_service = ConfigService()
        config = config_service.get_config()
        
        assert config.debug_mode is True
        
        # In debug mode, should use mock service
        if config.debug_mode:
            mock_client = MockSharePointService()
            service = IncidentService(sharepoint_client=mock_client)
            assert isinstance(service.sharepoint_client, MockSharePointService)

def test_production_mode_detection():
    """Test production mode detection from configuration."""
    from app.core.config import ConfigService
    from app.clients.sharepoint import SharePointClient
    from app.services.incident_service import IncidentService
    
    # Test debug mode disabled (production)
    with patch.dict(os.environ, {'DEBUG_MODE': 'false'}):
        config_service = ConfigService()
        config = config_service.get_config()
        
        assert config.debug_mode is False
        
        # In production mode, should use real SharePoint client
        if not config.debug_mode:
            real_client = SharePointClient()
            service = IncidentService(sharepoint_client=real_client)
            assert isinstance(service.sharepoint_client, SharePointClient)

def test_debug_mode_service_factory():
    """Test service factory pattern for debug vs production mode."""
    from app.core.config import ConfigService
    from app.services.mock_service import MockSharePointService
    from app.clients.sharepoint import SharePointClient
    
    def create_sharepoint_client(debug_mode: bool):
        """Factory function to create appropriate SharePoint client."""
        if debug_mode:
            return MockSharePointService()
        else:
            return SharePointClient()
    
    # Test factory with debug mode
    debug_client = create_sharepoint_client(debug_mode=True)
    assert isinstance(debug_client, MockSharePointService)
    
    # Test factory with production mode
    prod_client = create_sharepoint_client(debug_mode=False)
    assert isinstance(prod_client, SharePointClient)

def test_debug_logging_level_integration():
    """Test debug logging level integration."""
    from app.core.config import ConfigService
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    from unittest.mock import patch
    
    # Test with debug logging
    with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG', 'DEBUG_MODE': 'true'}):
        config_service = ConfigService()
        config = config_service.get_config()
        
        assert config.log_level == 'DEBUG'
        assert config.debug_mode is True
        
        # Mock service should log debug information
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
            callerLastName="Logging",
            callerTZ="123456789",
            callerPhone1="0501234567",
            callerEmail="debug@example.com",
            contactUsType="3"
        )
        
        with patch('app.services.mock_service.logger') as mock_logger:
            response = service.submit_incident(payload)
            
            # Should have logged in debug mode
            mock_logger.info.assert_called()

def test_environment_specific_mock_behavior():
    """Test mock behavior varies by environment."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    
    service = MockSharePointService()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Environment test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="ENV",
        callerFirstName="Environment",
        callerLastName="Test",
        callerTZ="111111111",
        callerPhone1="0501111111",
        callerEmail="env@example.com",
        contactUsType="3"
    )
    
    # Test development environment (success by default)
    with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
        response = service.submit_incident(payload)
        assert response.result_code == 200
    
    # Test staging environment (can simulate errors)
    with patch.dict(os.environ, {'ENVIRONMENT': 'staging'}):
        service.simulate_error("Staging test error", 400)
        response = service.submit_incident(payload)
        assert response.result_code == 400

def test_debug_mode_no_external_dependency():
    """Test debug mode has no external dependencies."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    import requests
    from unittest.mock import patch, MagicMock
    
    service = MockSharePointService()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="No external deps test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="NOEXT",
        callerFirstName="NoExternal",
        callerLastName="Deps",
        callerTZ="999999999",
        callerPhone1="0509999999",
        callerEmail="noext@example.com",
        contactUsType="3"
    )
    
    # Mock all external calls to ensure none are made
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('urllib.request.urlopen') as mock_urlopen:
        
        response = service.submit_incident(payload)
        
        # Should succeed without any external calls
        assert response.result_code == 200
        assert mock_get.call_count == 0
        assert mock_post.call_count == 0
        assert mock_urlopen.call_count == 0

def test_debug_mode_configuration_validation():
    """Test debug mode works with configuration validation."""
    from app.core.config import ConfigService
    from app.services.mock_service import MockSharePointService
    
    # Test valid debug configuration
    with patch.dict(os.environ, {
        'DEBUG_MODE': 'true',
        'ENVIRONMENT': 'development',
        'LOG_LEVEL': 'DEBUG',
        'PORT': '8000'
    }):
        config_service = ConfigService()
        config = config_service.get_config()
        
        # Configuration should be valid
        assert config.debug_mode is True
        assert config.environment == 'development'
        assert config.log_level == 'DEBUG'
        
        # Mock service should work with this configuration
        mock_service = MockSharePointService()
        assert mock_service is not None

def test_debug_ticket_id_format_validation():
    """Test debug ticket ID format meets requirements."""
    from app.services.mock_service import MockTicketGenerator
    import re
    import datetime
    
    generator = MockTicketGenerator()
    
    # Generate many tickets to test format consistency
    tickets = [generator.generate_ticket_id() for _ in range(100)]
    
    # All should match the required format
    pattern = r'^NETANYA-\d{4}-\d{6}$'
    for ticket in tickets:
        assert re.match(pattern, ticket), f"Ticket {ticket} doesn't match format"
    
    # All should contain current year
    current_year = str(datetime.datetime.now().year)
    for ticket in tickets:
        assert current_year in ticket
    
    # All should be unique
    assert len(set(tickets)) == len(tickets)

def test_debug_mode_with_hebrew_content():
    """Test debug mode handles Hebrew content properly."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    
    service = MockSharePointService()
    
    # Create payload with Hebrew content
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="תלונה דחופה על בעיה ברחוב הרצל",  # Hebrew complaint
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="15א",  # Hebrew house number
        callerFirstName="יוחנן",  # Hebrew first name
        callerLastName="כהן",  # Hebrew last name
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="yohanan@example.com",
        contactUsType="3"
    )
    
    # Submit with Hebrew content
    response = service.submit_incident(payload)
    
    # Should succeed with Hebrew content
    assert response.result_code == 200
    assert response.result_status == "SUCCESS CREATE"
    assert response.data.startswith("NETANYA-")

def test_debug_mode_error_scenarios():
    """Test debug mode can simulate various error scenarios."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    
    service = MockSharePointService()
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Error scenario test",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="ERR",
        callerFirstName="Error",
        callerLastName="Scenario",
        callerTZ="000000000",
        callerPhone1="0500000000",
        callerEmail="error@example.com",
        contactUsType="3"
    )
    
    # Test common SharePoint error scenarios
    error_scenarios = [
        (400, "Invalid request format"),
        (401, "Unauthorized access"),
        (403, "Forbidden operation"),
        (413, "Request entity too large"),
        (422, "Unprocessable entity"),
        (500, "Internal server error"),
        (502, "Bad gateway"),
        (503, "Service unavailable")
    ]
    
    for error_code, error_message in error_scenarios:
        service.simulate_error(error_message, error_code)
        response = service.submit_incident(payload)
        
        assert response.result_code == error_code
        assert response.error_description == error_message
        assert response.result_status == "ERROR"
        
        # Reset to success for next test
        service.simulate_success()

def test_debug_mode_performance():
    """Test debug mode performance characteristics."""
    from app.services.mock_service import MockSharePointService
    from app.models.sharepoint import APIPayload
    import time
    
    service = MockSharePointService()
    
    # Create multiple payloads for performance testing
    payloads = []
    for i in range(50):
        payload = APIPayload(
            eventCallSourceId=4,
            cityCode="7400",
            cityDesc="נתניה",
            eventCallCenterId="3",
            eventCallDesc=f"Performance test {i}",
            streetCode="898",
            streetDesc="קרל פופר",
            houseNumber=str(i),
            callerFirstName=f"Perf{i}",
            callerLastName="Test",
            callerTZ=f"{i:09d}",
            callerPhone1=f"050{i:07d}",
            callerEmail=f"perf{i}@example.com",
            contactUsType="3"
        )
        payloads.append(payload)
    
    # Measure performance
    start_time = time.time()
    responses = [service.submit_incident(payload) for payload in payloads]
    end_time = time.time()
    
    # Should be fast (debug mode should be faster than real API)
    total_time = end_time - start_time
    assert total_time < 1.0, f"Debug mode too slow: {total_time:.3f} seconds"
    
    # All should succeed
    assert all(response.result_code == 200 for response in responses)
    
    # All tickets should be unique
    tickets = [response.data for response in responses]
    assert len(set(tickets)) == len(tickets)
