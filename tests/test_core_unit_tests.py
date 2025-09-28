"""
Comprehensive unit tests for core components.
"""
import pytest
from pathlib import Path
import sys
import base64
from unittest.mock import patch, MagicMock

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
from app.models.response import APIResponse
from app.models.sharepoint import APIPayload
from app.core.config import ConfigService, AppConfig
from app.services.file_validation import FileValidationService, FileValidationError
from app.services.error_handling import ErrorHandlingService, CorrelationIdGenerator
from app.services.payload_transformation import PayloadTransformer
from pydantic import ValidationError


class TestUserDataValidation:
    """Test UserData model validation scenarios."""
    
    def test_valid_user_data(self):
        """Test valid user data creation."""
        user_data = UserData(
            first_name="יוסי",
            last_name="כהן",
            phone="0501234567",
            email="yossi@example.com"
        )
        assert user_data.first_name == "יוסי"
        assert user_data.last_name == "כהן"
        assert user_data.phone == "0501234567"
        assert user_data.email == "yossi@example.com"
    
    def test_user_data_without_optional_fields(self):
        """Test user data with only required fields."""
        user_data = UserData(
            first_name="מרים",
            last_name="לוי",
            phone="0521234567"
        )
        assert user_data.first_name == "מרים"
        assert user_data.email is None
        assert user_data.user_id is None
    
    def test_hebrew_text_handling(self):
        """Test Hebrew text is properly handled."""
        user_data = UserData(
            first_name="אליהו",
            last_name="בן-דוד",
            phone="0531234567"
        )
        assert user_data.first_name == "אליהו"
        assert user_data.last_name == "בן-דוד"


class TestCategoryValidation:
    """Test Category model validation scenarios."""
    
    def test_valid_category(self):
        """Test valid category creation."""
        category = Category(
            id=1,
            name="תאורה",
            text="Street lighting issues",
            image_url="https://example.com/lighting.jpg",
            event_call_desc="תאורת רחוב"
        )
        assert category.id == 1
        assert category.name == "תאורה"
        assert category.text == "Street lighting issues"
    
    def test_category_with_hebrew_content(self):
        """Test category with Hebrew content."""
        category = Category(
            id=2,
            name="ניקיון",
            text="Cleanliness and sanitation",
            image_url="https://example.com/clean.jpg",
            event_call_desc="ניקיון וחדשות"
        )
        assert category.name == "ניקיון"
        assert category.event_call_desc == "ניקיון וחדשות"


class TestImageFileValidation:
    """Test ImageFile model validation scenarios."""
    
    def test_valid_image_file(self):
        """Test valid image file creation."""
        test_data = b"test image data"
        encoded_data = base64.b64encode(test_data).decode('utf-8')
        
        image_file = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=len(test_data),
            data=encoded_data
        )
        
        assert image_file.filename == "test.jpg"
        assert image_file.content_type == "image/jpeg"
        assert image_file.size == len(test_data)
        assert image_file.data == encoded_data
    
    def test_image_file_with_png(self):
        """Test PNG image file."""
        test_data = b"PNG image data"
        encoded_data = base64.b64encode(test_data).decode('utf-8')
        
        image_file = ImageFile(
            filename="image.png",
            content_type="image/png",
            size=len(test_data),
            data=encoded_data
        )
        
        assert image_file.filename == "image.png"
        assert image_file.content_type == "image/png"


class TestIncidentSubmissionRequest:
    """Test IncidentSubmissionRequest model validation."""
    
    def test_complete_request(self):
        """Test complete incident submission request."""
        user_data = UserData(
            first_name="דוד",
            last_name="סמית",
            phone="0541234567",
            email="david@example.com"
        )
        
        category = Category(
            id=1,
            name="תאורה",
            text="Street lighting",
            image_url="https://example.com/light.jpg",
            event_call_desc="פנס רחוב"
        )
        
        street = StreetNumber(
            id=123,
            name="הרצל",
            image_url="https://example.com/street.jpg",
            house_number="15"
        )
        
        request = IncidentSubmissionRequest(
            user_data=user_data,
            category=category,
            street=street,
            custom_text="פנס רחוב לא עובד",
            extra_files=None
        )
        
        assert request.user_data.first_name == "דוד"
        assert request.category.name == "תאורה"
        assert request.street.name == "הרצל"
        assert request.custom_text == "פנס רחוב לא עובד"
    
    def test_request_with_image_file(self):
        """Test request with image attachment."""
        user_data = UserData(
            first_name="שרה",
            last_name="ברק",
            phone="0551234567"
        )
        
        category = Category(
            id=2,
            name="ניקיון",
            text="Cleanliness",
            image_url="https://example.com/clean.jpg",
            event_call_desc="ניקיון"
        )
        
        street = StreetNumber(
            id=456,
            name="בן גוריון",
            image_url="https://example.com/street2.jpg",
            house_number="20"
        )
        
        test_data = b"image data"
        encoded_data = base64.b64encode(test_data).decode('utf-8')
        
        image_file = ImageFile(
            filename="evidence.jpg",
            content_type="image/jpeg",
            size=len(test_data),
            data=encoded_data
        )
        
        request = IncidentSubmissionRequest(
            user_data=user_data,
            category=category,
            street=street,
            custom_text="זבל ברחוב",
            extra_files=image_file
        )
        
        assert request.extra_files is not None
        assert request.extra_files.filename == "evidence.jpg"


class TestConfigurationService:
    """Test configuration service functionality."""
    
    def test_config_service_initialization(self):
        """Test ConfigService can be initialized."""
        service = ConfigService()
        assert service is not None
    
    def test_get_config_returns_app_config(self):
        """Test get_config returns AppConfig instance."""
        service = ConfigService()
        config = service.get_config()
        assert isinstance(config, AppConfig)
    
    def test_sharepoint_endpoint_getter(self):
        """Test SharePoint endpoint getter."""
        service = ConfigService()
        endpoint = service.get_sharepoint_endpoint()
        assert isinstance(endpoint, str)
        assert len(endpoint) > 0
    
    @patch.dict('os.environ', {'ENVIRONMENT': 'production', 'DEBUG_MODE': 'false'})
    def test_production_configuration(self):
        """Test production environment configuration."""
        service = ConfigService()
        config = service.get_config()
        
        assert config.environment == "production"
        assert config.debug_mode is False
    
    @patch.dict('os.environ', {'ENVIRONMENT': 'development', 'DEBUG_MODE': 'true'})
    def test_development_configuration(self):
        """Test development environment configuration."""
        service = ConfigService()
        config = service.get_config()
        
        assert config.environment == "development"
        assert config.debug_mode is True


class TestFileValidationService:
    """Test file validation service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidationService()
    
    def test_valid_jpeg_validation(self):
        """Test valid JPEG file validation."""
        # JPEG file header
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        image_file = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=len(jpeg_data),
            data=base64.b64encode(jpeg_data).decode('utf-8')
        )
        
        result = self.validator.validate_file(image_file)
        assert result.is_valid is True
    
    def test_invalid_file_rejection(self):
        """Test invalid file is rejected."""
        # Non-image data
        fake_data = b"This is not an image"
        
        image_file = ImageFile(
            filename="fake.jpg",
            content_type="image/jpeg",
            size=len(fake_data),
            data=base64.b64encode(fake_data).decode('utf-8')
        )
        
        with pytest.raises(FileValidationError):
            self.validator.validate_file(image_file)
    
    def test_base64_validation(self):
        """Test base64 validation functionality."""
        valid_data = b"test data"
        valid_base64 = base64.b64encode(valid_data).decode('utf-8')
        
        result = self.validator.validate_base64(valid_base64)
        assert result.is_valid is True
        assert result.decoded_data == valid_data
    
    def test_invalid_base64_rejection(self):
        """Test invalid base64 is rejected."""
        invalid_base64 = "This is not base64!"
        
        with pytest.raises(FileValidationError):
            self.validator.validate_base64(invalid_base64)


class TestErrorHandlingService:
    """Test error handling service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_service = ErrorHandlingService()
    
    def test_correlation_id_generation(self):
        """Test correlation ID generation."""
        correlation_id = self.error_service.correlation_id_generator.generate_id()
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0
    
    def test_unique_correlation_ids(self):
        """Test that correlation IDs are unique."""
        id1 = self.error_service.correlation_id_generator.generate_id()
        id2 = self.error_service.correlation_id_generator.generate_id()
        assert id1 != id2
    
    def test_422_error_response_creation(self):
        """Test 422 error response creation."""
        field_errors = [
            {"field": "user_data.phone", "message": "Invalid phone format"}
        ]
        
        response = self.error_service.create_422_response(
            message="Validation failed",
            field_errors=field_errors,
            correlation_id="test-123"
        )
        
        assert response["error"] is True
        assert response["message"] == "Validation failed"
        assert response["correlation_id"] == "test-123"
        assert len(response["errors"]) == 1
    
    def test_500_error_response_creation(self):
        """Test 500 error response creation."""
        response = self.error_service.create_500_response(
            message="Internal server error",
            error_details="Database connection failed",
            correlation_id="test-456"
        )
        
        assert response["error"] is True
        assert response["message"] == "Internal server error"
        assert response["correlation_id"] == "test-456"


class TestPayloadTransformation:
    """Test payload transformation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = PayloadTransformer()
    
    def test_basic_transformation(self):
        """Test basic request to API payload transformation."""
        user_data = UserData(
            first_name="יוסי",
            last_name="כהן",
            phone="0501234567",
            email="yossi@example.com"
        )
        
        category = Category(
            id=1,
            name="תאורה",
            text="Street lighting",
            image_url="https://example.com/light.jpg",
            event_call_desc="פנס רחוב לא עובד"
        )
        
        street = StreetNumber(
            id=123,
            name="הרצל",
            image_url="https://example.com/street.jpg",
            house_number="15"
        )
        
        request = IncidentSubmissionRequest(
            user_data=user_data,
            category=category,
            street=street,
            custom_text="פנס רחוב שבור",
            extra_files=None
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Check fixed values
        assert payload.eventCallSourceId == 4
        assert payload.cityCode == "7400"
        assert payload.cityDesc == "נתניה"
        
        # Check mapped values
        assert payload.callerFirstName == "יוסי"
        assert payload.callerLastName == "כהן"
        assert payload.callerPhone1 == "0501234567"
    
    def test_transformation_with_custom_text(self):
        """Test transformation includes custom text."""
        user_data = UserData(
            first_name="מרים",
            last_name="לוי",
            phone="0521234567"
        )
        
        category = Category(
            id=2,
            name="ניקיון",
            text="Cleanliness",
            image_url="https://example.com/clean.jpg",
            event_call_desc="בעיית ניקיון"
        )
        
        street = StreetNumber(
            id=456,
            name="בן גוריון",
            image_url="https://example.com/street2.jpg",
            house_number="20"
        )
        
        request = IncidentSubmissionRequest(
            user_data=user_data,
            category=category,
            street=street,
            custom_text="זבל צבור בפינת הרחוב",
            extra_files=None
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Custom text should be included in description
        assert "זבל צבור בפינת הרחוב" in payload.eventCallDesc


class TestResponseModels:
    """Test response model functionality."""
    
    def test_api_response_success(self):
        """Test successful API response."""
        response = APIResponse(
            ResultCode=200,
            ErrorDescription="",
            ResultStatus="SUCCESS CREATE",
            data="NETANYA-2025-123456"
        )
        
        assert response.ResultCode == 200
        assert response.ErrorDescription == ""
        assert response.ResultStatus == "SUCCESS CREATE"
        assert response.data == "NETANYA-2025-123456"
    
    def test_api_response_error(self):
        """Test error API response."""
        response = APIResponse(
            ResultCode=400,
            ErrorDescription="Invalid request data",
            ResultStatus="ERROR",
            data=""
        )
        
        assert response.ResultCode == 400
        assert response.ErrorDescription == "Invalid request data"
        assert response.ResultStatus == "ERROR"
        assert response.data == ""


class TestAPIPayloadModel:
    """Test API payload model for SharePoint."""
    
    def test_valid_api_payload(self):
        """Test valid API payload creation."""
        payload = APIPayload(
            eventCallSourceId=4,
            cityCode="7400",
            cityDesc="נתניה",
            eventCallCenterId="3",
            eventCallDesc="פנס רחוב לא עובד",
            streetCode="123",
            streetDesc="הרצל",
            houseNumber="15",
            callerFirstName="יוסי",
            callerLastName="כהן",
            callerTZ="",
            callerPhone1="0501234567",
            callerEmail="",
            contactUsType="3"
        )
        
        assert payload.eventCallSourceId == 4
        assert payload.cityCode == "7400"
        assert payload.cityDesc == "נתניה"
        assert payload.eventCallDesc == "פנס רחוב לא עובד"
        assert payload.callerFirstName == "יוסי"
    
    def test_api_payload_serialization(self):
        """Test API payload can be serialized."""
        payload = APIPayload(
            eventCallSourceId=4,
            cityCode="7400",
            cityDesc="נתניה",
            eventCallCenterId="3",
            eventCallDesc="Test incident",
            streetCode="456",
            streetDesc="בן גוריון",
            houseNumber="20",
            callerFirstName="מרים",
            callerLastName="לוי",
            callerTZ="",
            callerPhone1="0521234567",
            callerEmail="",
            contactUsType="3"
        )
        
        serialized = payload.model_dump()
        assert serialized["eventCallSourceId"] == 4
        assert serialized["cityDesc"] == "נתניה"
        assert serialized["callerFirstName"] == "מרים"


class TestIntegrationScenarios:
    """Test integration scenarios between components."""
    
    def test_complete_workflow_simulation(self):
        """Test complete workflow from request to payload."""
        # 1. Create request
        user_data = UserData(
            first_name="אליהו",
            last_name="בן-צבי",
            phone="0591234567",
            email="eli@example.com"
        )
        
        category = Category(
            id=3,
            name="תחבורה",
            text="Transportation",
            image_url="https://example.com/transport.jpg",
            event_call_desc="בעיית תנועה"
        )
        
        street = StreetNumber(
            id=789,
            name="ויצמן",
            image_url="https://example.com/street3.jpg",
            house_number="30"
        )
        
        request = IncidentSubmissionRequest(
            user_data=user_data,
            category=category,
            street=street,
            custom_text="בור גדול בכביש",
            extra_files=None
        )
        
        # 2. Transform to API payload
        transformer = PayloadTransformer()
        payload = transformer.transform_to_api_payload(request)
        
        # 3. Verify end-to-end transformation
        assert payload.callerFirstName == "אליהו"
        assert payload.callerLastName == "בן-צבי"
        assert payload.streetDesc == "ויצמן"
        assert payload.houseNumber == "30"
        assert "בור גדול בכביש" in payload.eventCallDesc
    
    def test_error_handling_integration(self):
        """Test error handling integration."""
        error_service = ErrorHandlingService()
        
        # Generate correlation ID
        correlation_id = error_service.correlation_id_generator.generate_id()
        
        # Create error response
        response = error_service.create_422_response(
            message="Validation failed",
            field_errors=[{"field": "test", "message": "test error"}],
            correlation_id=correlation_id
        )
        
        assert response["correlation_id"] == correlation_id
        assert response["error"] is True
