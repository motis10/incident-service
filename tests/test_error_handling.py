"""
Test request validation and error handling framework.
"""
import pytest
import uuid
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_error_handler_service_import():
    """Test that error handling service can be imported."""
    try:
        from app.services.error_handling import (
            ErrorHandlingService, ValidationErrorResponse,
            ErrorDetails, CorrelationIdGenerator
        )
        assert ErrorHandlingService is not None
        assert ValidationErrorResponse is not None
        assert ErrorDetails is not None
        assert CorrelationIdGenerator is not None
    except ImportError:
        pytest.fail("Could not import error handling service")

def test_correlation_id_generation():
    """Test correlation ID generation for request tracking."""
    from app.services.error_handling import CorrelationIdGenerator
    
    generator = CorrelationIdGenerator()
    
    # Generate multiple correlation IDs
    ids = [generator.generate() for _ in range(10)]
    
    # All should be unique
    assert len(set(ids)) == 10
    
    # All should be valid UUIDs or similar format
    for correlation_id in ids:
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0
        # Should be UUID-like format
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Generated correlation ID is not a valid UUID: {correlation_id}")

def test_validation_error_response_structure():
    """Test structure of validation error responses."""
    from app.services.error_handling import ValidationErrorResponse, ErrorDetails
    
    error_details = [
        ErrorDetails(
            field="user_data.first_name",
            message="Field required",
            type="missing"
        ),
        ErrorDetails(
            field="user_data.phone",
            message="Invalid phone number format",
            type="value_error"
        )
    ]
    
    response = ValidationErrorResponse(
        error="Validation failed",
        details=error_details,
        correlation_id="test-correlation-123"
    )
    
    assert response.error == "Validation failed"
    assert len(response.details) == 2
    assert response.correlation_id == "test-correlation-123"
    
    # Check first error detail
    first_error = response.details[0]
    assert first_error.field == "user_data.first_name"
    assert first_error.message == "Field required"
    assert first_error.type == "missing"

def test_pydantic_validation_error_conversion():
    """Test conversion of Pydantic validation errors to structured format."""
    from app.services.error_handling import ErrorHandlingService
    from app.models.request import UserData
    from pydantic import ValidationError
    
    service = ErrorHandlingService()
    
    # Create invalid data that will cause Pydantic validation errors
    try:
        UserData()  # Missing required fields
    except ValidationError as e:
        response = service.handle_validation_error(e)
        
        assert isinstance(response, dict)
        assert "error" in response
        assert "details" in response
        assert "correlation_id" in response
        
        # Should have details for missing required fields
        details = response["details"]
        assert len(details) > 0
        
        # Check that required fields are mentioned
        field_names = [detail["field"] for detail in details]
        assert any("first_name" in field for field in field_names)
        assert any("last_name" in field for field in field_names)
        assert any("phone" in field for field in field_names)

def test_file_validation_error_handling():
    """Test handling of file validation errors."""
    from app.services.error_handling import ErrorHandlingService
    from app.services.file_validation import ValidationResult
    
    service = ErrorHandlingService()
    
    # Create file validation failure
    validation_result = ValidationResult(
        is_valid=False,
        errors=[
            "Unsupported file format: application/pdf",
            "File size (20971520 bytes) exceeds maximum allowed size of 10.0MB"
        ]
    )
    
    response = service.handle_file_validation_error(validation_result)
    
    assert isinstance(response, dict)
    assert "error" in response
    assert "details" in response
    assert "correlation_id" in response
    
    details = response["details"]
    assert len(details) == 2
    
    # Check error details
    assert details[0]["field"] == "extra_files"
    assert "format" in details[0]["message"].lower()
    assert details[1]["field"] == "extra_files"
    assert "size" in details[1]["message"].lower()

def test_http_422_error_structure():
    """Test HTTP 422 error response structure."""
    from app.services.error_handling import ErrorHandlingService
    
    service = ErrorHandlingService()
    
    # Test generic 422 error
    response = service.create_422_response(
        message="Validation failed",
        field_errors=[
            {"field": "category.id", "message": "Invalid category ID", "type": "value_error"}
        ]
    )
    
    assert response["error"] == "Validation failed"
    assert response["status_code"] == 422
    assert len(response["details"]) == 1
    assert "correlation_id" in response

def test_http_500_error_structure():
    """Test HTTP 500 error response structure."""
    from app.services.error_handling import ErrorHandlingService
    
    service = ErrorHandlingService()
    
    # Test internal server error
    response = service.create_500_response(
        message="Internal server error occurred",
        error_details="Database connection failed"
    )
    
    assert response["error"] == "Internal server error occurred"
    assert response["status_code"] == 500
    assert "correlation_id" in response
    assert "timestamp" in response

def test_http_400_error_structure():
    """Test HTTP 400 error response structure."""
    from app.services.error_handling import ErrorHandlingService
    
    service = ErrorHandlingService()
    
    # Test bad request error
    response = service.create_400_response(
        message="Invalid JSON format"
    )
    
    assert response["error"] == "Invalid JSON format"
    assert response["status_code"] == 400
    assert "correlation_id" in response

def test_error_logging_with_correlation_id():
    """Test error logging includes correlation ID for tracing."""
    from app.services.error_handling import ErrorHandlingService
    import logging
    from unittest.mock import patch
    
    service = ErrorHandlingService()
    
    with patch('app.services.error_handling.logger') as mock_logger:
        correlation_id = "test-123"
        service.log_error(
            message="Test error occurred",
            correlation_id=correlation_id,
            error_details={"key": "value"}
        )
        
        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        
        # Check that correlation ID is in the log message
        assert correlation_id in str(log_call)

def test_field_level_error_details():
    """Test detailed field-level error information."""
    from app.services.error_handling import ErrorHandlingService, ErrorDetails
    
    service = ErrorHandlingService()
    
    # Test field-specific error details
    field_errors = [
        ErrorDetails(
            field="user_data.email",
            message="Invalid email format",
            type="value_error"
        ),
        ErrorDetails(
            field="street.house_number",
            message="House number cannot be empty",
            type="missing"
        )
    ]
    
    response = service.create_field_validation_response(field_errors)
    
    assert len(response["details"]) == 2
    
    # Check email error
    email_error = next(d for d in response["details"] if "email" in d["field"])
    assert email_error["message"] == "Invalid email format"
    assert email_error["type"] == "value_error"
    
    # Check house number error
    house_error = next(d for d in response["details"] if "house_number" in d["field"])
    assert house_error["message"] == "House number cannot be empty"
    assert house_error["type"] == "missing"

def test_nested_validation_error_handling():
    """Test handling of nested model validation errors."""
    from app.services.error_handling import ErrorHandlingService
    from app.models.request import IncidentSubmissionRequest
    from pydantic import ValidationError
    
    service = ErrorHandlingService()
    
    # Create invalid nested data
    invalid_data = {
        "user_data": {
            # Missing required fields
        },
        "category": {
            "id": "invalid_id",  # Should be int
            "name": "",  # Empty name
        },
        "street": {
            # Missing required fields
        }
    }
    
    try:
        IncidentSubmissionRequest(**invalid_data)
    except ValidationError as e:
        response = service.handle_validation_error(e)
        
        # Should handle nested errors properly
        assert len(response["details"]) > 0
        
        # Check that nested field paths are correct
        field_paths = [detail["field"] for detail in response["details"]]
        assert any("user_data" in field for field in field_paths)
        assert any("category" in field for field in field_paths)
        assert any("street" in field for field in field_paths)

def test_error_response_serialization():
    """Test that error responses can be properly serialized to JSON."""
    from app.services.error_handling import ErrorHandlingService
    import json
    
    service = ErrorHandlingService()
    
    response = service.create_422_response(
        message="Validation error",
        field_errors=[
            {"field": "test_field", "message": "Test message", "type": "test_type"}
        ]
    )
    
    # Should be JSON serializable
    json_str = json.dumps(response)
    assert isinstance(json_str, str)
    
    # Should be deserializable back
    deserialized = json.loads(json_str)
    assert deserialized["error"] == "Validation error"
    assert deserialized["status_code"] == 422

def test_correlation_id_propagation():
    """Test that correlation IDs are properly propagated through error handling."""
    from app.services.error_handling import ErrorHandlingService
    
    service = ErrorHandlingService()
    
    # Test with existing correlation ID
    existing_id = "existing-correlation-123"
    
    response = service.create_422_response(
        message="Test error",
        field_errors=[],
        correlation_id=existing_id
    )
    
    assert response["correlation_id"] == existing_id
    
    # Test without correlation ID (should generate new one)
    response_auto = service.create_422_response(
        message="Test error",
        field_errors=[]
    )
    
    assert "correlation_id" in response_auto
    assert response_auto["correlation_id"] != existing_id

def test_comprehensive_error_handling_workflow():
    """Test complete error handling workflow from validation to response."""
    from app.services.error_handling import ErrorHandlingService
    from app.models.request import IncidentSubmissionRequest
    from pydantic import ValidationError
    
    service = ErrorHandlingService()
    
    # Simulate complete validation failure scenario
    try:
        # Invalid request with multiple errors
        IncidentSubmissionRequest(
            user_data={"first_name": ""},  # Empty required field
            category={"id": -1},  # Invalid/incomplete data
            street={}  # Missing required fields
        )
    except ValidationError as e:
        # Handle the error
        response = service.handle_validation_error(e)
        
        # Verify complete response structure
        assert "error" in response
        assert "details" in response
        assert "correlation_id" in response
        assert "timestamp" in response
        
        # Should have multiple error details
        assert len(response["details"]) > 0
        
        # All details should have required fields
        for detail in response["details"]:
            assert "field" in detail
            assert "message" in detail
            assert "type" in detail
        
        # Should have proper timestamp format
        timestamp = response["timestamp"]
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format
