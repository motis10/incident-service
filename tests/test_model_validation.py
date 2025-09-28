"""
Additional validation tests for Pydantic models.
Tests edge cases, constraints, and validation rules.
"""
import pytest
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_user_data_phone_validation():
    """Test phone number validation patterns."""
    from app.models.request import UserData
    from pydantic import ValidationError
    
    # Valid phone numbers
    valid_phones = [
        "0501234567",  # Israeli mobile
        "0507654321",  # Israeli mobile  
        "021234567",   # Israeli landline
        "+972501234567"  # International format
    ]
    
    for phone in valid_phones:
        user = UserData(
            first_name="Test",
            last_name="User",
            phone=phone
        )
        assert user.phone == phone

def test_user_data_empty_strings():
    """Test handling of empty strings in optional fields."""
    from app.models.request import UserData
    
    user = UserData(
        first_name="John",
        last_name="Doe",
        phone="0501234567",
        user_id="",  # Empty string
        email=""     # Empty string
    )
    
    assert user.user_id == ""
    assert user.email == ""

def test_category_id_validation():
    """Test category ID validation."""
    from app.models.request import Category
    from pydantic import ValidationError
    
    # Valid category
    category = Category(
        id=1,
        name="Test Category",
        text="Test description",
        image_url="https://example.com/image.jpg",
        event_call_desc="Test event description"
    )
    assert category.id == 1
    
    # Test negative ID (should be allowed for flexibility)
    category_negative = Category(
        id=-1,
        name="Test Category",
        text="Test description", 
        image_url="https://example.com/image.jpg",
        event_call_desc="Test event description"
    )
    assert category_negative.id == -1

def test_street_number_validation():
    """Test street number validation."""
    from app.models.request import StreetNumber
    
    # Test various house number formats
    house_numbers = ["123", "123A", "123/4", "123-125", "בניין 5"]
    
    for house_num in house_numbers:
        street = StreetNumber(
            id=1,
            name="Test Street",
            image_url="https://example.com/street.jpg",
            house_number=house_num
        )
        assert street.house_number == house_num

def test_image_file_size_validation():
    """Test image file size validation."""
    from app.models.request import ImageFile
    
    # Test various file sizes
    sizes = [0, 1024, 1048576, 10485760]  # 0B, 1KB, 1MB, 10MB
    
    for size in sizes:
        image = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=size,
            data="base64data=="
        )
        assert image.size == size

def test_image_file_content_types():
    """Test supported image content types."""
    from app.models.request import ImageFile
    
    # Test supported MIME types
    supported_types = [
        "image/jpeg",
        "image/png", 
        "image/gif",
        "image/webp"
    ]
    
    for content_type in supported_types:
        image = ImageFile(
            filename=f"test.{content_type.split('/')[-1]}",
            content_type=content_type,
            size=1024,
            data="base64data=="
        )
        assert image.content_type == content_type

def test_incident_submission_minimal():
    """Test incident submission with minimal required data."""
    from app.models.request import (
        IncidentSubmissionRequest, UserData, Category, StreetNumber
    )
    
    # Minimal user data
    user = UserData(
        first_name="John",
        last_name="Doe", 
        phone="0501234567"
    )
    
    # Minimal category
    category = Category(
        id=1,
        name="Test",
        text="Test category",
        image_url="",
        event_call_desc="Test description"
    )
    
    # Minimal street
    street = StreetNumber(
        id=1,
        name="Test Street",
        image_url="",
        house_number="1"
    )
    
    # Minimal submission (no custom text, no files)
    submission = IncidentSubmissionRequest(
        user_data=user,
        category=category,
        street=street
    )
    
    assert submission.custom_text is None
    assert submission.extra_files is None

def test_api_response_error_cases():
    """Test API response for error scenarios."""
    from app.models.response import APIResponse
    
    # Test various error codes
    error_responses = [
        (400, "Bad Request", "ERROR", ""),
        (422, "Validation Error", "VALIDATION_FAILED", ""),
        (500, "Internal Server Error", "INTERNAL_ERROR", ""),
        (502, "SharePoint Unavailable", "EXTERNAL_ERROR", "")
    ]
    
    for code, description, status, data in error_responses:
        response = APIResponse(
            ResultCode=code,
            ErrorDescription=description,
            ResultStatus=status,
            data=data
        )
        
        assert response.ResultCode == code
        assert response.ErrorDescription == description
        assert response.ResultStatus == status
        assert response.data == data

def test_api_payload_fixed_values():
    """Test that APIPayload enforces correct fixed values."""
    from app.models.sharepoint import APIPayload
    
    # Test with correct fixed values
    payload = APIPayload(
        eventCallSourceId=4,      # Must be 4
        cityCode="7400",          # Must be 7400  
        cityDesc="נתניה",         # Must be נתניה
        eventCallCenterId="3",    # Must be 3
        streetCode="898",         # Must be 898
        streetDesc="קרל פופר",    # Must be קרל פופר
        contactUsType="3",        # Must be 3
        eventCallDesc="Test complaint",
        houseNumber="123",
        callerFirstName="John",
        callerLastName="Doe",
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="john@example.com"
    )
    
    # Verify fixed values
    assert payload.eventCallSourceId == 4
    assert payload.cityCode == "7400"
    assert payload.cityDesc == "נתניה"
    assert payload.eventCallCenterId == "3"
    assert payload.streetCode == "898"
    assert payload.streetDesc == "קרל פופר"
    assert payload.contactUsType == "3"

def test_nested_model_validation():
    """Test validation of nested models."""
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    from pydantic import ValidationError
    
    # Test with invalid nested UserData
    with pytest.raises(ValidationError) as exc_info:
        IncidentSubmissionRequest(
            user_data={"invalid": "data"},  # Invalid UserData structure
            category=Category(
                id=1, name="Test", text="Test", 
                image_url="", event_call_desc="Test"
            ),
            street=StreetNumber(
                id=1, name="Test St", image_url="", house_number="1"
            )
        )
    
    # Should contain validation errors for UserData fields
    errors = exc_info.value.errors()
    user_data_errors = [e for e in errors if e['loc'][0] == 'user_data']
    assert len(user_data_errors) > 0

def test_unicode_support():
    """Test Unicode support in text fields."""
    from app.models.request import UserData, Category, StreetNumber
    from app.models.sharepoint import APIPayload
    
    # Test Hebrew names and descriptions
    user = UserData(
        first_name="יוחנן",
        last_name="כהן",
        phone="0501234567"
    )
    
    category = Category(
        id=1,
        name="ניקיון רחובות",
        text="בעיות ניקיון ברחובות העיר",
        image_url="https://example.com/image.jpg",
        event_call_desc="תלונה על ניקיון רחובות"
    )
    
    street = StreetNumber(
        id=1,
        name="רחוב הרצל",
        image_url="https://example.com/street.jpg", 
        house_number="15א"
    )
    
    # Test Hebrew in SharePoint payload
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="תלונה על זבל ברחוב",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="15א",
        callerFirstName="יוחנן",
        callerLastName="כהן",
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="yohanan@example.com",
        contactUsType="3"
    )
    
    assert user.first_name == "יוחנן"
    assert category.name == "ניקיון רחובות"
    assert street.name == "רחוב הרצל"
    assert payload.callerFirstName == "יוחנן"
    assert payload.eventCallDesc == "תלונה על זבל ברחוב"
