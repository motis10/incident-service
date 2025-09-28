"""
Integration tests for payload transformation with complete service workflows.
"""
import pytest
import base64
from unittest.mock import patch, Mock
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_complete_request_to_sharepoint_workflow():
    """Test complete workflow from request validation to SharePoint submission."""
    from app.services.payload_transformation import PayloadTransformer
    from app.clients.sharepoint import SharePointClient
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    from app.services.file_validation import FileValidationService
    from app.services.error_handling import ErrorHandlingService
    
    # Initialize all services
    transformer = PayloadTransformer()
    sharepoint_client = SharePointClient()
    file_service = FileValidationService()
    error_service = ErrorHandlingService()
    
    # Create complete incident request with file
    test_image_data = b"fake_jpeg_content_for_testing"
    base64_data = base64.b64encode(test_image_data).decode('utf-8')
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Complete",
            last_name="Integration",
            phone="0501234567",
            user_id="123456789",
            email="complete@example.com"
        ),
        category=Category(
            id=1,
            name="Street Maintenance",
            text="Street maintenance issues",
            image_url="https://example.com/street.jpg",
            event_call_desc="Street maintenance complaint"
        ),
        street=StreetNumber(
            id=1,
            name="Integration Street",
            image_url="https://example.com/integration.jpg",
            house_number="42"
        ),
        custom_text="Complete integration test with custom description",
        extra_files=ImageFile(
            filename="evidence.jpg",
            content_type="image/jpeg",
            size=len(test_image_data),
            data=base64_data
        )
    )
    
    # 1. Validate file
    file_validation = file_service.validate_file(request.extra_files)
    assert file_validation.is_valid
    
    # 2. Prepare multipart file
    multipart_file = file_service.prepare_multipart_file(request.extra_files)
    
    # 3. Transform to SharePoint payload
    payload = transformer.transform_to_sharepoint(request)
    
    # Verify transformation
    assert payload.callerFirstName == "Complete"
    assert payload.callerLastName == "Integration"
    assert payload.eventCallDesc == "Complete integration test with custom description"
    assert payload.cityDesc == "נתניה"  # Fixed municipality value
    
    # 4. Submit to SharePoint (mocked)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "INTEGRATION-SUCCESS-123"
    }
    
    with patch.object(sharepoint_client.session, 'post', return_value=mock_response):
        result = sharepoint_client.submit_to_sharepoint(payload, file=multipart_file)
        
        assert result.ResultCode == 200
        assert result.data == "INTEGRATION-SUCCESS-123"

def test_transformation_with_validation_errors():
    """Test payload transformation integration with validation error handling."""
    from app.services.payload_transformation import PayloadTransformer, TransformationError
    from app.services.error_handling import ErrorHandlingService
    
    transformer = PayloadTransformer()
    error_service = ErrorHandlingService()
    
    # Test transformation error handling
    try:
        transformer.transform_to_sharepoint(None)
        pytest.fail("Should have raised TransformationError")
    except TransformationError as e:
        # Handle transformation error with error service
        error_response = error_service.create_500_response(
            message="Payload transformation failed",
            error_details=str(e)
        )
        
        assert error_response["status_code"] == 500
        assert "correlation_id" in error_response
        assert "request cannot be none" in error_response["details"].lower()

def test_municipality_values_consistency():
    """Test that municipality fixed values are consistent across all transformations."""
    from app.services.payload_transformation import PayloadTransformer, NetanyaMuniConfig
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    config = NetanyaMuniConfig()
    
    # Create different requests
    requests = []
    for i in range(5):
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name=f"User{i}",
                last_name=f"Test{i}",
                phone=f"05011111{i}{i}"
            ),
            category=Category(
                id=i,
                name=f"Category{i}",
                text=f"Category {i} description",
                image_url=f"https://example.com/cat{i}.jpg",
                event_call_desc=f"Category {i} complaint"
            ),
            street=StreetNumber(
                id=i,
                name=f"Street {i}",
                image_url=f"https://example.com/street{i}.jpg",
                house_number=str(i * 10)
            )
        )
        requests.append(request)
    
    # Transform all requests
    payloads = [transformer.transform_to_sharepoint(req) for req in requests]
    
    # All should have identical municipality values
    for payload in payloads:
        assert payload.eventCallSourceId == config.event_call_source_id
        assert payload.cityCode == config.city_code
        assert payload.cityDesc == config.city_desc
        assert payload.eventCallCenterId == config.event_call_center_id
        assert payload.streetCode == config.street_code
        assert payload.streetDesc == config.street_desc
        assert payload.contactUsType == config.contact_us_type

def test_custom_text_vs_category_priority():
    """Test priority handling between custom text and category descriptions."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    base_request_data = {
        "user_data": UserData(
            first_name="Priority",
            last_name="Test",
            phone="0505555555"
        ),
        "category": Category(
            id=1,
            name="Priority Test",
            text="Priority test category",
            image_url="https://example.com/priority.jpg",
            event_call_desc="Default category description"
        ),
        "street": StreetNumber(
            id=1,
            name="Priority Street",
            image_url="https://example.com/priority_street.jpg",
            house_number="999"
        )
    }
    
    # Test 1: Custom text takes priority
    request_with_custom = IncidentSubmissionRequest(
        **base_request_data,
        custom_text="Custom text should override category"
    )
    payload1 = transformer.transform_to_sharepoint(request_with_custom)
    assert payload1.eventCallDesc == "Custom text should override category"
    
    # Test 2: Empty custom text falls back to category
    request_empty_custom = IncidentSubmissionRequest(
        **base_request_data,
        custom_text=""
    )
    payload2 = transformer.transform_to_sharepoint(request_empty_custom)
    assert payload2.eventCallDesc == "Default category description"
    
    # Test 3: No custom text falls back to category
    request_no_custom = IncidentSubmissionRequest(**base_request_data)
    payload3 = transformer.transform_to_sharepoint(request_no_custom)
    assert payload3.eventCallDesc == "Default category description"
    
    # Test 4: Whitespace-only custom text falls back to category
    request_whitespace = IncidentSubmissionRequest(
        **base_request_data,
        custom_text="   \t\n   "
    )
    payload4 = transformer.transform_to_sharepoint(request_whitespace)
    assert payload4.eventCallDesc == "Default category description"

def test_hebrew_content_end_to_end():
    """Test complete Hebrew content handling from request to SharePoint."""
    from app.services.payload_transformation import PayloadTransformer
    from app.clients.sharepoint import SharePointClient
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    client = SharePointClient()
    
    # Create request with comprehensive Hebrew content
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="שרה",
            last_name="כהן",
            phone="0508765432",
            user_id="987654321",
            email="sarah.cohen@example.com"
        ),
        category=Category(
            id=1,
            name="ניקיון רחובות",
            text="בעיות ניקיון ברחובות העיר",
            image_url="https://example.com/cleaning_he.jpg",
            event_call_desc="תלונה כללית על ניקיון"
        ),
        street=StreetNumber(
            id=1,
            name="רחוב בן גוריון",
            image_url="https://example.com/ben_gurion.jpg",
            house_number="25ג"
        ),
        custom_text="תלונה דחופה על פח זבל שבור שגורם לזיהום סביבתי ליד הבניין שלי"
    )
    
    # Transform to SharePoint
    payload = transformer.transform_to_sharepoint(request)
    
    # Verify Hebrew text preservation
    assert payload.callerFirstName == "שרה"
    assert payload.callerLastName == "כהן"
    assert payload.houseNumber == "25ג"
    assert payload.eventCallDesc == "תלונה דחופה על פח זבל שבור שגורם לזיהום סביבתי ליד הבניין שלי"
    
    # Verify fixed Hebrew municipality values
    assert payload.cityDesc == "נתניה"
    assert payload.streetDesc == "קרל פופר"
    
    # Test multipart request generation with Hebrew content
    multipart_request = client.build_multipart_request(payload)
    body_str = multipart_request.body.decode('utf-8')
    
    # Hebrew content should be properly encoded
    assert "שרה" in body_str
    assert "כהן" in body_str
    assert "תלונה דחופה" in body_str
    assert "נתניה" in body_str

def test_optional_fields_handling_integration():
    """Test integration with optional fields in various combinations."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    # Test various combinations of optional fields
    test_cases = [
        # Minimal required fields only
        {
            "user_data": UserData(
                first_name="Minimal",
                last_name="User",
                phone="0501111111"
            ),
            "expected_tz": "",
            "expected_email": ""
        },
        # With user_id but no email
        {
            "user_data": UserData(
                first_name="WithID",
                last_name="User",
                phone="0502222222",
                user_id="123456789"
            ),
            "expected_tz": "123456789",
            "expected_email": ""
        },
        # With email but no user_id
        {
            "user_data": UserData(
                first_name="WithEmail",
                last_name="User",
                phone="0503333333",
                email="email@example.com"
            ),
            "expected_tz": "",
            "expected_email": "email@example.com"
        },
        # With both optional fields
        {
            "user_data": UserData(
                first_name="Complete",
                last_name="User",
                phone="0504444444",
                user_id="987654321",
                email="complete@example.com"
            ),
            "expected_tz": "987654321",
            "expected_email": "complete@example.com"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        request = IncidentSubmissionRequest(
            user_data=test_case["user_data"],
            category=Category(
                id=i,
                name=f"Test{i}",
                text=f"Test case {i}",
                image_url=f"https://example.com/test{i}.jpg",
                event_call_desc=f"Test case {i} description"
            ),
            street=StreetNumber(
                id=i,
                name=f"Test Street {i}",
                image_url=f"https://example.com/street{i}.jpg",
                house_number=str(i * 100)
            )
        )
        
        payload = transformer.transform_to_sharepoint(request)
        
        # Verify optional fields handling
        assert payload.callerTZ == test_case["expected_tz"]
        assert payload.callerEmail == test_case["expected_email"]
        
        # Required fields should always be present
        assert payload.callerFirstName is not None
        assert payload.callerLastName is not None
        assert payload.callerPhone1 is not None

def test_transformation_performance():
    """Test payload transformation performance with multiple requests."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    import time
    
    transformer = PayloadTransformer()
    
    # Create multiple requests for performance testing
    requests = []
    for i in range(100):
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name=f"Performance{i}",
                last_name=f"Test{i}",
                phone=f"050{i:07d}",
                user_id=f"{i:09d}",
                email=f"perf{i}@example.com"
            ),
            category=Category(
                id=i % 10,
                name=f"Category{i % 10}",
                text=f"Performance test category {i % 10}",
                image_url=f"https://example.com/perf{i % 10}.jpg",
                event_call_desc=f"Performance test {i % 10}"
            ),
            street=StreetNumber(
                id=i % 5,
                name=f"Performance Street {i % 5}",
                image_url=f"https://example.com/perfstreet{i % 5}.jpg",
                house_number=str(i)
            ),
            custom_text=f"Performance test custom text {i}"
        )
        requests.append(request)
    
    # Measure transformation time
    start_time = time.time()
    payloads = [transformer.transform_to_sharepoint(req) for req in requests]
    end_time = time.time()
    
    # Verify all transformations succeeded
    assert len(payloads) == 100
    
    # Performance should be reasonable (less than 1 second for 100 transformations)
    total_time = end_time - start_time
    assert total_time < 1.0, f"Transformation took too long: {total_time:.3f} seconds"
    
    # Verify data integrity
    for i, payload in enumerate(payloads):
        assert payload.callerFirstName == f"Performance{i}"
        assert payload.eventCallDesc == f"Performance test custom text {i}"
        assert payload.cityDesc == "נתניה"  # Fixed value should be consistent

def test_configuration_customization():
    """Test payload transformation with custom NetanyaMuni configuration."""
    from app.services.payload_transformation import PayloadTransformer, NetanyaMuniConfig
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    # Create custom configuration (for testing purposes)
    custom_config = NetanyaMuniConfig()
    custom_config.city_code = "TEST"
    custom_config.city_desc = "Test City"
    
    transformer = PayloadTransformer(config=custom_config)
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Config",
            last_name="Test",
            phone="0509999999"
        ),
        category=Category(
            id=1,
            name="Config Test",
            text="Configuration test",
            image_url="https://example.com/config.jpg",
            event_call_desc="Configuration test description"
        ),
        street=StreetNumber(
            id=1,
            name="Config Street",
            image_url="https://example.com/config_street.jpg",
            house_number="CONFIG"
        )
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Should use custom configuration values
    assert payload.cityCode == "TEST"
    assert payload.cityDesc == "Test City"
    
    # Other fixed values should remain from default config
    assert payload.eventCallSourceId == 4
    assert payload.contactUsType == "3"

def test_transformation_logging_integration():
    """Test payload transformation logging integration."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    from unittest.mock import patch
    
    transformer = PayloadTransformer()
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Logging",
            last_name="Test",
            phone="0508888888"
        ),
        category=Category(
            id=1,
            name="Logging Test",
            text="Logging test category",
            image_url="https://example.com/logging.jpg",
            event_call_desc="Logging test description"
        ),
        street=StreetNumber(
            id=1,
            name="Logging Street",
            image_url="https://example.com/logging_street.jpg",
            house_number="LOG"
        )
    )
    
    # Capture log messages
    with patch('app.services.payload_transformation.logger') as mock_logger:
        payload = transformer.transform_to_sharepoint(request)
        
        # Should have logged transformation
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        
        # Log should include relevant information
        assert "Logging Test" in log_call
        assert "caller=Logging Test" in log_call
        assert "house_number=LOG" in log_call
