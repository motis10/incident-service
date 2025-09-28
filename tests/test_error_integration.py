"""
Integration tests for error handling with complete service workflows.
"""
import pytest
import base64
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_complete_validation_error_workflow():
    """Test complete validation error workflow from request to response."""
    from app.services.error_handling import ErrorHandlingService
    from app.services.file_validation import FileValidationService
    from app.models.request import IncidentSubmissionRequest, ImageFile
    from pydantic import ValidationError
    
    error_service = ErrorHandlingService()
    file_service = FileValidationService()
    
    # Test scenario: Invalid request with file validation errors
    invalid_image = ImageFile(
        filename="invalid_file.exe",
        content_type="application/x-executable",  # Unsupported
        size=50 * 1024 * 1024,  # Too large (50MB)
        data="invalid_base64_data!@#"  # Invalid base64
    )
    
    # Test Pydantic validation error
    try:
        IncidentSubmissionRequest(
            user_data={},  # Missing required fields
            category={"id": "invalid"},  # Wrong type
            street={},  # Missing required fields
            extra_files=invalid_image
        )
    except ValidationError as e:
        pydantic_response = error_service.handle_validation_error(e)
        
        # Should have structured validation errors
        assert "correlation_id" in pydantic_response
        assert len(pydantic_response["details"]) > 0
    
    # Test file validation error
    file_validation_result = file_service.validate_file(invalid_image)
    file_response = error_service.handle_file_validation_error(file_validation_result)
    
    # Should have file-specific errors
    assert "correlation_id" in file_response
    assert len(file_response["details"]) > 0
    assert all(detail["field"] == "extra_files" for detail in file_response["details"])

def test_error_response_consistency():
    """Test that all error responses have consistent structure."""
    from app.services.error_handling import ErrorHandlingService, ErrorDetails
    
    service = ErrorHandlingService()
    
    # Test different error types
    responses = [
        service.create_400_response("Bad request"),
        service.create_422_response("Validation failed", []),
        service.create_500_response("Internal error"),
        service.create_field_validation_response([
            ErrorDetails("test_field", "Test error", "test_type")
        ])
    ]
    
    # All should have consistent structure
    for response in responses:
        assert "error" in response
        assert "correlation_id" in response
        assert "timestamp" in response
        
        # Correlation IDs should be unique
        correlation_ids = [r["correlation_id"] for r in responses]
        assert len(set(correlation_ids)) == len(correlation_ids)

def test_error_logging_integration():
    """Test error logging integration with correlation tracking."""
    from app.services.error_handling import ErrorHandlingService
    from app.models.request import UserData
    from pydantic import ValidationError
    import logging
    from unittest.mock import patch
    
    service = ErrorHandlingService()
    
    # Capture log messages
    with patch('app.services.error_handling.logger') as mock_logger:
        try:
            UserData()  # Missing required fields
        except ValidationError as e:
            response = service.handle_validation_error(e)
            
            # Should have logged the error
            mock_logger.error.assert_called_once()
            
            # Log should include correlation ID
            log_call_args = mock_logger.error.call_args
            correlation_id = response["correlation_id"]
            assert correlation_id in str(log_call_args)

def test_nested_error_field_paths():
    """Test that nested validation errors have correct field paths."""
    from app.services.error_handling import ErrorHandlingService
    from app.models.request import IncidentSubmissionRequest
    from pydantic import ValidationError
    
    service = ErrorHandlingService()
    
    # Create nested validation errors
    try:
        IncidentSubmissionRequest(
            user_data={
                "first_name": "",  # Empty required field
                "phone": "invalid_phone"  # Invalid format (if we had validation)
            },
            category={
                "id": "not_a_number",  # Should be int
                "name": ""  # Empty
            },
            street={}  # Missing all fields
        )
    except ValidationError as e:
        response = service.handle_validation_error(e)
        
        # Check field paths are correctly formatted
        field_paths = [detail["field"] for detail in response["details"]]
        
        # Should have nested paths
        assert any("user_data." in path for path in field_paths)
        assert any("category." in path for path in field_paths)
        assert any("street." in path for path in field_paths)
        
        # Specific field checks
        category_id_errors = [d for d in response["details"] if "category.id" in d["field"]]
        assert len(category_id_errors) > 0

def test_error_message_localization_ready():
    """Test that error messages are structured for potential localization."""
    from app.services.error_handling import ErrorHandlingService, ErrorDetails
    
    service = ErrorHandlingService()
    
    # Create errors with different types
    field_errors = [
        ErrorDetails("field1", "Field required", "missing"),
        ErrorDetails("field2", "Invalid format", "value_error"),
        ErrorDetails("field3", "Too long", "value_error.too_long")
    ]
    
    response = service.create_field_validation_response(field_errors)
    
    # Each error should have type for localization
    for detail in response["details"]:
        assert "type" in detail
        assert "message" in detail
        assert "field" in detail
        
        # Type should be structured for localization keys
        assert isinstance(detail["type"], str)
        assert len(detail["type"]) > 0

def test_file_and_validation_error_combination():
    """Test handling multiple error types in combination."""
    from app.services.error_handling import ErrorHandlingService
    from app.services.file_validation import FileValidationService, ValidationResult
    from app.models.request import UserData
    from pydantic import ValidationError
    
    error_service = ErrorHandlingService()
    
    # Simulate both validation and file errors
    correlation_id = error_service.correlation_generator.generate()
    
    # File validation error
    file_result = ValidationResult(
        is_valid=False,
        errors=["File too large", "Invalid format"]
    )
    file_response = error_service.handle_file_validation_error(
        file_result, 
        correlation_id=correlation_id
    )
    
    # Pydantic validation error
    try:
        UserData()
    except ValidationError as e:
        validation_response = error_service.handle_validation_error(
            e, 
            correlation_id=correlation_id
        )
    
    # Both should use the same correlation ID for tracking
    assert file_response["correlation_id"] == correlation_id
    assert validation_response["correlation_id"] == correlation_id

def test_error_response_json_serialization():
    """Test that complex error responses serialize properly to JSON."""
    from app.services.error_handling import ErrorHandlingService
    from app.models.request import IncidentSubmissionRequest
    from pydantic import ValidationError
    import json
    
    service = ErrorHandlingService()
    
    # Create complex validation error
    try:
        IncidentSubmissionRequest(
            user_data={"first_name": "יוחנן"},  # Hebrew text
            category={"id": "invalid", "name": "קטגוריה"},  # Mixed invalid/Hebrew
            street={}
        )
    except ValidationError as e:
        response = service.handle_validation_error(e)
        
        # Should serialize to JSON without issues
        json_str = json.dumps(response, ensure_ascii=False)
        assert isinstance(json_str, str)
        
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized["correlation_id"] == response["correlation_id"]
        assert len(deserialized["details"]) == len(response["details"])

def test_correlation_id_uniqueness_across_requests():
    """Test that correlation IDs are unique across multiple requests."""
    from app.services.error_handling import ErrorHandlingService
    
    service = ErrorHandlingService()
    
    # Generate multiple errors
    responses = []
    for i in range(20):
        response = service.create_400_response(f"Test error {i}")
        responses.append(response)
    
    # All correlation IDs should be unique
    correlation_ids = [r["correlation_id"] for r in responses]
    assert len(set(correlation_ids)) == len(correlation_ids)
    
    # All should be valid UUIDs
    import uuid
    for correlation_id in correlation_ids:
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Invalid UUID format: {correlation_id}")

def test_error_timestamp_format():
    """Test that error timestamps are in proper ISO format."""
    from app.services.error_handling import ErrorHandlingService
    from datetime import datetime
    
    service = ErrorHandlingService()
    
    response = service.create_422_response("Test error", [])
    timestamp = response["timestamp"]
    
    # Should be valid ISO format
    try:
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed_time, datetime)
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {timestamp}")
    
    # Should be recent (within last minute)
    from datetime import timezone
    now = datetime.now(timezone.utc)
    time_diff = now - parsed_time.replace(tzinfo=timezone.utc)
    assert time_diff.total_seconds() < 60  # Should be very recent

def test_production_error_handling():
    """Test error handling appropriate for production environments."""
    from app.services.error_handling import ErrorHandlingService
    
    service = ErrorHandlingService()
    
    # Test 500 error (should not leak internal details in production)
    response = service.create_500_response(
        message="Internal server error",
        error_details="Database connection string: secret_info"
    )
    
    # Should have generic error message
    assert response["error"] == "Internal server error"
    assert response["status_code"] == 500
    
    # Should have correlation ID for internal tracking
    assert "correlation_id" in response
    
    # Details should be present but controlled
    assert "details" in response
