"""
Enhanced unit tests for Pydantic model validation and error scenarios.
"""
import pytest
from pathlib import Path
import sys
from typing import Dict, Any
import base64

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
from app.models.response import SubmissionResult, ErrorDetail, ErrorResponse
from app.models.sharepoint import APIPayload
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
    
    def test_empty_name_validation(self):
        """Test validation fails for empty names."""
        with pytest.raises(ValidationError) as exc_info:
            UserData(
                first_name="",
                last_name="כהן",
                phone="0501234567",
                email="yossi@example.com"
            )
        
        errors = exc_info.value.errors()
        assert any(error['type'] == 'value_error' for error in errors)
    
    def test_invalid_phone_format(self):
        """Test validation fails for invalid phone format."""
        invalid_phones = [
            "123",           # Too short
            "050123456789",  # Too long
            "abc1234567",    # Contains letters
            "050-123-4567",  # Contains dashes
            "",              # Empty
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                UserData(
                    first_name="יוסי",
                    last_name="כהן",
                    phone=phone,
                    email="yossi@example.com"
                )
    
    def test_invalid_email_format(self):
        """Test validation fails for invalid email format."""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user space@domain.com",
            "",
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                UserData(
                    first_name="יוסי",
                    last_name="כהן",
                    phone="0501234567",
                    email=email
                )
    
    def test_hebrew_text_validation(self):
        """Test Hebrew text is properly handled."""
        user_data = UserData(
            first_name="מרים",
            last_name="לוי",
            phone="0521234567",
            email="miriam@example.com"
        )
        assert user_data.first_name == "מרים"
        assert user_data.last_name == "לוי"
    
    def test_mixed_language_names(self):
        """Test mixed Hebrew/English names."""
        user_data = UserData(
            first_name="David דוד",
            last_name="Smith סמית",
            phone="0531234567",
            email="david@example.com"
        )
        assert user_data.first_name == "David דוד"
        assert user_data.last_name == "Smith סמית"


class TestIncidentCategoryValidation:
    """Test IncidentCategory model validation scenarios."""
    
    def test_valid_categories(self):
        """Test all valid incident categories."""
        valid_categories = [
            ("תאורה", "Street lighting issues"),
            ("ניקיון", "Cleanliness and sanitation"),
            ("תחבורה", "Transportation and traffic"),
            ("גינון", "Parks and landscaping"),
            ("מדרכות", "Sidewalks and walkways"),
            ("אחר", "Other municipal issues")
        ]
        
        for name, description in valid_categories:
            category = IncidentCategory(name=name, description=description)
            assert category.name == name
            assert category.description == description
    
    def test_empty_category_name(self):
        """Test validation fails for empty category name."""
        with pytest.raises(ValidationError):
            IncidentCategory(name="", description="Test description")
    
    def test_empty_category_description(self):
        """Test validation fails for empty category description."""
        with pytest.raises(ValidationError):
            IncidentCategory(name="תאורה", description="")
    
    def test_long_category_names(self):
        """Test validation for very long category names."""
        long_name = "א" * 101  # 101 Hebrew characters
        with pytest.raises(ValidationError):
            IncidentCategory(name=long_name, description="Test description")


class TestImageFileValidation:
    """Test ImageFile model validation scenarios."""
    
    def test_valid_image_file(self):
        """Test valid image file creation."""
        # Create a simple test image data
        test_data = b"test image data"
        encoded_data = base64.b64encode(test_data).decode('utf-8')
        
        image_file = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=len(test_data),
            data=test_data
        )
        
        assert image_file.filename == "test.jpg"
        assert image_file.content_type == "image/jpeg"
        assert image_file.size == len(test_data)
        assert image_file.data == test_data
    
    def test_invalid_content_types(self):
        """Test validation fails for invalid content types."""
        invalid_types = [
            "text/plain",
            "application/pdf",
            "video/mp4",
            "audio/mp3",
            "",
        ]
        
        test_data = b"test data"
        
        for content_type in invalid_types:
            with pytest.raises(ValidationError):
                ImageFile(
                    filename="test.jpg",
                    content_type=content_type,
                    size=len(test_data),
                    data=test_data
                )
    
    def test_file_size_validation(self):
        """Test file size validation."""
        test_data = b"x" * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte
        
        with pytest.raises(ValidationError):
            ImageFile(
                filename="large.jpg",
                content_type="image/jpeg",
                size=len(test_data),
                data=test_data
            )
    
    def test_filename_validation(self):
        """Test filename validation."""
        invalid_filenames = [
            "",
            "file.txt",           # Wrong extension
            "file.exe",           # Executable
            "file without extension",
            "../../../etc/passwd.jpg",  # Path traversal attempt
        ]
        
        test_data = b"test data"
        
        for filename in invalid_filenames:
            with pytest.raises(ValidationError):
                ImageFile(
                    filename=filename,
                    content_type="image/jpeg",
                    size=len(test_data),
                    data=test_data
                )


class TestIncidentSubmissionRequestValidation:
    """Test IncidentSubmissionRequest model validation scenarios."""
    
    def test_complete_valid_request(self):
        """Test complete valid incident submission request."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="יוסי",
                last_name="כהן",
                phone="0501234567",
                email="yossi@example.com"
            ),
            category=IncidentCategory(
                name="תאורה",
                description="Street lighting issues"
            ),
            description="פנס רחוב לא עובד ברחוב הרצל 5",
            address="רחוב הרצל 5, נתניה",
            extra_files=None
        )
        
        assert request.user_data.first_name == "יוסי"
        assert request.category.name == "תאורה"
        assert request.description == "פנס רחוב לא עובד ברחוב הרצל 5"
        assert request.address == "רחוב הרצל 5, נתניה"
        assert request.extra_files is None
    
    def test_request_with_file(self):
        """Test incident request with file attachment."""
        test_data = b"test image data"
        
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="מרים",
                last_name="לוי",
                phone="0521234567",
                email="miriam@example.com"
            ),
            category=IncidentCategory(
                name="ניקיון",
                description="Cleanliness and sanitation"
            ),
            description="זבל בפארק",
            address="פארק העצמאות, נתניה",
            extra_files=ImageFile(
                filename="garbage.jpg",
                content_type="image/jpeg",
                size=len(test_data),
                data=test_data
            )
        )
        
        assert request.extra_files is not None
        assert request.extra_files.filename == "garbage.jpg"
    
    def test_description_validation(self):
        """Test description field validation."""
        # Test minimum length
        with pytest.raises(ValidationError):
            IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="יוסי",
                    last_name="כהן",
                    phone="0501234567",
                    email="yossi@example.com"
                ),
                category=IncidentCategory(
                    name="תאורה",
                    description="Street lighting issues"
                ),
                description="קצר",  # Too short
                address="רחוב הרצל 5, נתניה"
            )
        
        # Test maximum length
        long_description = "ת" * 1001  # 1001 characters
        with pytest.raises(ValidationError):
            IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="יוסי",
                    last_name="כהן",
                    phone="0501234567",
                    email="yossi@example.com"
                ),
                category=IncidentCategory(
                    name="תאורה",
                    description="Street lighting issues"
                ),
                description=long_description,
                address="רחוב הרצל 5, נתניה"
            )
    
    def test_address_validation(self):
        """Test address field validation."""
        with pytest.raises(ValidationError):
            IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="יוסי",
                    last_name="כהן",
                    phone="0501234567",
                    email="yossi@example.com"
                ),
                category=IncidentCategory(
                    name="תאורה",
                    description="Street lighting issues"
                ),
                description="פנס רחוב לא עובד",
                address=""  # Empty address
            )


class TestAPIPayloadValidation:
    """Test APIPayload model validation scenarios."""
    
    def test_valid_api_payload(self):
        """Test valid API payload creation."""
        payload = APIPayload(
            eventCallSourceId=4,
            cityCode="7400",
            cityDesc="נתניה",
            eventCallCenterId="3",
            eventCallDesc="פנס רחוב לא עובד ברחוב הרצל 5",
            streetCode="123",
            streetDesc="הרצל",
            houseNumber="5",
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
        assert payload.eventCallDesc == "פנס רחוב לא עובד ברחוב הרצל 5"
    
    def test_required_fields_validation(self):
        """Test validation fails when required fields are missing."""
        with pytest.raises(ValidationError):
            APIPayload(
                # Missing eventCallSourceId
                cityCode="7400",
                cityDesc="נתניה",
                eventCallCenterId="3",
                eventCallDesc="Test description",
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
    
    def test_field_type_validation(self):
        """Test field type validation."""
        with pytest.raises(ValidationError):
            APIPayload(
                eventCallSourceId="invalid",  # Should be int
                cityCode="7400",
                cityDesc="נתניה",
                eventCallCenterId="3",
                eventCallDesc="Test description",
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


class TestResponseModelValidation:
    """Test response model validation scenarios."""
    
    def test_submission_result_success(self):
        """Test successful submission result."""
        result = SubmissionResult(
            success=True,
            ticket_id="NETANYA-2025-123456",
            correlation_id="corr-123",
            has_file=False,
            file_info=None,
            metadata={"test": "value"}
        )
        
        assert result.success is True
        assert result.ticket_id == "NETANYA-2025-123456"
        assert result.correlation_id == "corr-123"
        assert result.has_file is False
        assert result.file_info is None
        assert result.metadata == {"test": "value"}
    
    def test_submission_result_with_file(self):
        """Test submission result with file information."""
        result = SubmissionResult(
            success=True,
            ticket_id="NETANYA-2025-123456",
            correlation_id="corr-123",
            has_file=True,
            file_info={
                "filename": "test.jpg",
                "size": 1024,
                "content_type": "image/jpeg"
            },
            metadata={}
        )
        
        assert result.has_file is True
        assert result.file_info["filename"] == "test.jpg"
    
    def test_error_detail_validation(self):
        """Test ErrorDetail model validation."""
        error = ErrorDetail(
            field="user_data.email",
            message="Invalid email format",
            invalid_value="not-an-email"
        )
        
        assert error.field == "user_data.email"
        assert error.message == "Invalid email format"
        assert error.invalid_value == "not-an-email"
    
    def test_error_response_validation(self):
        """Test ErrorResponse model validation."""
        error_response = ErrorResponse(
            error=True,
            message="Validation failed",
            correlation_id="corr-123",
            errors=[
                ErrorDetail(
                    field="user_data.phone",
                    message="Invalid phone format",
                    invalid_value="123"
                )
            ]
        )
        
        assert error_response.error is True
        assert error_response.message == "Validation failed"
        assert error_response.correlation_id == "corr-123"
        assert len(error_response.errors) == 1
        assert error_response.errors[0].field == "user_data.phone"


class TestModelSerialization:
    """Test model serialization and deserialization scenarios."""
    
    def test_incident_request_serialization(self):
        """Test incident request can be serialized to/from dict."""
        request_data = {
            "user_data": {
                "first_name": "יוסי",
                "last_name": "כהן",
                "phone": "0501234567",
                "email": "yossi@example.com"
            },
            "category": {
                "name": "תאורה",
                "description": "Street lighting issues"
            },
            "description": "פנס רחוב לא עובד ברחוב הרצל 5",
            "address": "רחוב הרצל 5, נתניה"
        }
        
        # Test deserialization
        request = IncidentSubmissionRequest(**request_data)
        assert request.user_data.first_name == "יוסי"
        
        # Test serialization
        serialized = request.model_dump()
        assert serialized["user_data"]["first_name"] == "יוסי"
    
    def test_api_payload_serialization(self):
        """Test API payload serialization for SharePoint API."""
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
        
        serialized = payload.model_dump()
        assert serialized["eventCallSourceId"] == 4
        assert serialized["cityCode"] == "7400"
        assert serialized["cityDesc"] == "נתניה"
    
    def test_unicode_handling(self):
        """Test proper Unicode handling in models."""
        user_data = UserData(
            first_name="אליה",
            last_name="בן-דוד",
            phone="0501234567",
            email="elijah@example.com"
        )
        
        # Test round-trip serialization preserves Unicode
        serialized = user_data.model_dump()
        deserialized = UserData(**serialized)
        
        assert deserialized.first_name == "אליה"
        assert deserialized.last_name == "בן-דוד"
