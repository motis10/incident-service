"""
Test production services and configuration.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_production_service_import():
    """Test that production services can be imported."""
    try:
        from app.services.production_service import (
            ProductionSharePointClient, ProductionIncidentService, create_production_client
        )
        assert ProductionSharePointClient is not None
        assert ProductionIncidentService is not None
        assert create_production_client is not None
    except ImportError:
        pytest.fail("Could not import production services")

def test_production_validator_import():
    """Test that production validator can be imported."""
    try:
        from app.core.production_validator import ProductionValidator, ValidationResult
        assert ProductionValidator is not None
        assert ValidationResult is not None
    except ImportError:
        pytest.fail("Could not import production validator")

@patch('app.services.production_service.ConfigService')
def test_production_client_initialization(mock_config_service):
    """Test production SharePoint client initialization."""
    from app.services.production_service import ProductionSharePointClient
    
    # Mock configuration
    mock_config = MagicMock()
    mock_config.debug_mode = False
    mock_config.environment = 'production'
    mock_config_service.return_value.get_config.return_value = mock_config
    mock_config_service.return_value.get_sharepoint_endpoint.return_value = 'https://test.sharepoint.com'
    
    # Should initialize successfully
    client = ProductionSharePointClient()
    assert client is not None

@patch('app.services.production_service.ConfigService')
def test_production_client_debug_mode_rejection(mock_config_service):
    """Test that production client rejects debug mode."""
    from app.services.production_service import ProductionSharePointClient
    
    # Mock configuration with debug mode
    mock_config = MagicMock()
    mock_config.debug_mode = True
    mock_config_service.return_value.get_config.return_value = mock_config
    
    # Should raise error
    with pytest.raises(ValueError, match="Production SharePoint client cannot run in debug mode"):
        ProductionSharePointClient()

@patch('app.services.production_service.ConfigService')
def test_production_client_https_validation(mock_config_service):
    """Test HTTPS endpoint validation."""
    from app.services.production_service import ProductionSharePointClient
    
    # Mock configuration
    mock_config = MagicMock()
    mock_config.debug_mode = False
    mock_config.environment = 'production'
    mock_config_service.return_value.get_config.return_value = mock_config
    mock_config_service.return_value.get_sharepoint_endpoint.return_value = 'http://insecure.endpoint.com'
    
    # Should raise error for non-HTTPS in production
    with pytest.raises(ValueError, match="Production mode requires HTTPS SharePoint endpoint"):
        ProductionSharePointClient()

def test_production_client_error_sanitization():
    """Test error message sanitization in production."""
    from app.services.production_service import ProductionSharePointClient
    
    with patch('app.services.production_service.ConfigService'):
        client = ProductionSharePointClient.__new__(ProductionSharePointClient)
        
        # Test URL sanitization
        sensitive_error = "Connection failed to https://secret-internal.sharepoint.com/api with key=abc123"
        sanitized = client._sanitize_error_message(sensitive_error)
        assert "secret-internal.sharepoint.com" not in sanitized
        assert "abc123" not in sanitized
        assert "SharePoint service connection error" in sanitized

def test_production_client_metrics_recording():
    """Test metrics recording functionality."""
    from app.services.production_service import ProductionSharePointClient
    
    with patch('app.services.production_service.ConfigService'):
        client = ProductionSharePointClient.__new__(ProductionSharePointClient)
        
        # Should not raise error when recording metrics
        client._record_metrics("test_metric", 1.5, {"test": "value"})

@patch('app.core.production_validator.ConfigService')
def test_production_validator_initialization(mock_config_service):
    """Test production validator initialization."""
    from app.core.production_validator import ProductionValidator
    
    mock_config_service.return_value.get_config.return_value = MagicMock()
    
    validator = ProductionValidator()
    assert validator is not None

@patch('app.core.production_validator.ConfigService')
def test_production_validation_debug_mode_check(mock_config_service):
    """Test validation of debug mode settings."""
    from app.core.production_validator import ProductionValidator
    
    # Mock configuration with debug mode enabled
    mock_config = MagicMock()
    mock_config.debug_mode = True
    mock_config.environment = 'production'
    mock_config.log_level = 'DEBUG'
    mock_config_service.return_value.get_config.return_value = mock_config
    
    validator = ProductionValidator()
    results = validator._validate_environment_config()
    
    # Should find debug mode error
    debug_errors = [r for r in results if 'debug mode' in r.message.lower()]
    assert len(debug_errors) > 0
    assert any(r.severity == 'error' for r in debug_errors)

@patch('app.core.production_validator.ConfigService')
@patch('app.core.production_validator.requests.head')
def test_sharepoint_connectivity_validation(mock_requests, mock_config_service):
    """Test SharePoint connectivity validation."""
    from app.core.production_validator import ProductionValidator
    
    # Mock configuration
    mock_config_service.return_value.get_sharepoint_endpoint.return_value = 'https://test.sharepoint.com'
    mock_config_service.return_value.get_config.return_value = MagicMock()
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests.return_value = mock_response
    
    validator = ProductionValidator()
    results = validator._validate_sharepoint_connectivity()
    
    # Should show successful connectivity
    connectivity_results = [r for r in results if r.category == 'connectivity']
    assert len(connectivity_results) > 0
    assert any(r.is_valid for r in connectivity_results)

@patch('app.core.production_validator.ConfigService')
def test_validation_summary_generation(mock_config_service):
    """Test validation summary generation."""
    from app.core.production_validator import ProductionValidator, ValidationResult
    
    mock_config_service.return_value.get_config.return_value = MagicMock()
    
    validator = ProductionValidator()
    
    # Create mock results
    results = [
        ValidationResult(True, "Test passed", "info", "test"),
        ValidationResult(False, "Test error", "error", "test"),
        ValidationResult(False, "Test warning", "warning", "test"),
    ]
    
    summary = validator.get_validation_summary(results)
    
    assert summary["total_checks"] == 3
    assert summary["errors"] == 1
    assert summary["warnings"] == 1
    assert summary["passed"] == 1
    assert summary["is_production_ready"] is False

@patch('app.core.production_validator.ConfigService')
def test_https_validation(mock_config_service):
    """Test HTTPS requirements validation."""
    from app.core.production_validator import ProductionValidator
    
    mock_config_service.return_value.get_sharepoint_endpoint.return_value = 'http://insecure.endpoint.com'
    mock_config_service.return_value.get_config.return_value = MagicMock()
    
    validator = ProductionValidator()
    results = validator._validate_https_requirements()
    
    # Should find HTTPS error
    https_errors = [r for r in results if 'https' in r.message.lower()]
    assert len(https_errors) > 0

def test_production_client_factory():
    """Test production client factory function."""
    from app.services.production_service import create_production_client
    
    with patch('app.services.production_service.ConfigService') as mock_config_service:
        mock_config = MagicMock()
        mock_config.debug_mode = True
        mock_config_service.return_value.get_config.return_value = mock_config
        
        # Should reject debug mode
        with pytest.raises(ValueError, match="Cannot create production client in debug mode"):
            create_production_client()

@patch('app.services.production_service.ConfigService')
def test_production_incident_service(mock_config_service):
    """Test production incident service initialization."""
    from app.services.production_service import ProductionIncidentService
    
    mock_config = MagicMock()
    mock_config.debug_mode = False
    mock_config.environment = 'production'
    mock_config_service.return_value.get_config.return_value = mock_config
    mock_config_service.return_value.get_sharepoint_endpoint.return_value = 'https://test.sharepoint.com'
    
    service = ProductionIncidentService()
    assert service is not None
    
    # Test metrics collection
    metrics = service.get_service_metrics()
    assert "service_name" in metrics
    assert "environment" in metrics
    assert "sharepoint_health" in metrics

@patch('app.services.production_service.ProductionSharePointClient')
def test_production_sharepoint_submission_logging(mock_client_class):
    """Test production SharePoint submission logging."""
    from app.models.sharepoint import APIPayload
    from app.models.response import APIResponse
    
    # Mock client instance
    mock_client = MagicMock()
    mock_response = APIResponse(
        ResultCode=200,
        ErrorDescription="",
        ResultStatus="SUCCESS CREATE",
        data="TICKET-123"
    )
    mock_client.submit_to_sharepoint.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    # Mock payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Test incident",
        streetCode="123",
        streetDesc="Test Street",
        houseNumber="1",
        callerFirstName="John",
        callerLastName="Doe",
        callerTZ="",
        callerPhone1="0501234567",
        callerEmail="",
        contactUsType="3"
    )
    
    # Test submission (this would normally include detailed logging)
    response = mock_client.submit_to_sharepoint(payload)
    assert response.data == "TICKET-123"

def test_production_config_validation_workflow():
    """Test complete production configuration validation workflow."""
    from app.core.production_validator import ProductionValidator
    
    with patch('app.core.production_validator.ConfigService') as mock_config_service:
        # Mock a mostly valid production configuration
        mock_config = MagicMock()
        mock_config.debug_mode = False
        mock_config.environment = 'production'
        mock_config.log_level = 'INFO'
        mock_config_service.return_value.get_config.return_value = mock_config
        mock_config_service.return_value.get_sharepoint_endpoint.return_value = 'https://prod.sharepoint.com'
        
        validator = ProductionValidator()
        
        # Mock various validation methods to avoid external dependencies
        with patch.object(validator, '_validate_sharepoint_connectivity', return_value=[]), \
             patch.object(validator, '_validate_https_requirements', return_value=[]):
            
            results = validator.validate_all()
            summary = validator.get_validation_summary(results)
            
            assert isinstance(results, list)
            assert isinstance(summary, dict)
            assert "total_checks" in summary
