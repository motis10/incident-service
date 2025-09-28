"""
Test Pydantic data models for API contracts.
"""
import pytest
from typing import Optional
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_models_import():
    """Test that all models can be imported."""
    try:
        from app.models.request import (
            IncidentSubmissionRequest, UserData, Category, 
            StreetNumber, ImageFile
        )
        from app.models.response import APIResponse
        from app.models.sharepoint import APIPayload
        
        assert IncidentSubmissionRequest is not None
        assert UserData is not None
        assert Category is not None
        assert StreetNumber is not None
        assert ImageFile is not None
        assert APIResponse is not None
        assert APIPayload is not None
    except ImportError:
        pytest.fail("Could not import all required models")

def test_user_data_model():
    """Test UserData model validation."""
    from app.models.request import UserData
    
    # Valid user data
    valid_user = UserData(
        first_name="John",
        last_name="Doe", 
        phone="0501234567",
        user_id="123456789",
        email="john.doe@example.com"
    )
    
    assert valid_user.first_name == "John"
    assert valid_user.last_name == "Doe"
    assert valid_user.phone == "0501234567"
    assert valid_user.user_id == "123456789"
    assert valid_user.email == "john.doe@example.com"

def test_user_data_required_fields():
    """Test UserData model required field validation."""
    from app.models.request import UserData
    from pydantic import ValidationError
    
    # Missing required fields should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        UserData()
    
    errors = exc_info.value.errors()
    required_fields = {error['loc'][0] for error in errors}
    
    # Check that required fields are validated
    assert 'first_name' in required_fields
    assert 'last_name' in required_fields
    assert 'phone' in required_fields

def test_user_data_optional_fields():
    """Test UserData model with only required fields."""
    from app.models.request import UserData
    
    # Minimal valid user data
    user = UserData(
        first_name="Jane",
        last_name="Smith",
        phone="0521234567"
    )
    
    assert user.first_name == "Jane"
    assert user.last_name == "Smith"
    assert user.phone == "0521234567"
    assert user.user_id is None
    assert user.email is None

def test_category_model():
    """Test Category model validation."""
    from app.models.request import Category
    
    valid_category = Category(
        id=1,
        name="Street Cleaning",
        text="Street cleaning issues",
        image_url="https://example.com/image.jpg",
        event_call_desc="Street cleaning complaint"
    )
    
    assert valid_category.id == 1
    assert valid_category.name == "Street Cleaning"
    assert valid_category.text == "Street cleaning issues"
    assert valid_category.image_url == "https://example.com/image.jpg"
    assert valid_category.event_call_desc == "Street cleaning complaint"

def test_street_number_model():
    """Test StreetNumber model validation."""
    from app.models.request import StreetNumber
    
    valid_street = StreetNumber(
        id=1,
        name="Main Street",
        image_url="https://example.com/street.jpg",
        house_number="123"
    )
    
    assert valid_street.id == 1
    assert valid_street.name == "Main Street"
    assert valid_street.image_url == "https://example.com/street.jpg"
    assert valid_street.house_number == "123"

def test_image_file_model():
    """Test ImageFile model validation."""
    from app.models.request import ImageFile
    
    valid_image = ImageFile(
        filename="test.jpg",
        content_type="image/jpeg",
        size=1024,
        data="base64encodeddata=="
    )
    
    assert valid_image.filename == "test.jpg"
    assert valid_image.content_type == "image/jpeg"
    assert valid_image.size == 1024
    assert valid_image.data == "base64encodeddata=="

def test_incident_submission_request_model():
    """Test IncidentSubmissionRequest model validation."""
    from app.models.request import (
        IncidentSubmissionRequest, UserData, Category, 
        StreetNumber, ImageFile
    )
    
    user_data = UserData(
        first_name="John",
        last_name="Doe",
        phone="0501234567"
    )
    
    category = Category(
        id=1,
        name="Street Cleaning",
        text="Street cleaning issues",
        image_url="https://example.com/image.jpg",
        event_call_desc="Street cleaning complaint"
    )
    
    street = StreetNumber(
        id=1,
        name="Main Street",
        image_url="https://example.com/street.jpg",
        house_number="123"
    )
    
    # Valid submission without file
    submission = IncidentSubmissionRequest(
        user_data=user_data,
        category=category,
        street=street,
        custom_text="Test complaint"
    )
    
    assert submission.user_data == user_data
    assert submission.category == category
    assert submission.street == street
    assert submission.custom_text == "Test complaint"
    assert submission.extra_files is None

def test_incident_submission_with_file():
    """Test IncidentSubmissionRequest with image file."""
    from app.models.request import (
        IncidentSubmissionRequest, UserData, Category, 
        StreetNumber, ImageFile
    )
    
    user_data = UserData(first_name="John", last_name="Doe", phone="0501234567")
    category = Category(id=1, name="Test", text="Test", image_url="", event_call_desc="Test")
    street = StreetNumber(id=1, name="Test St", image_url="", house_number="1")
    
    image_file = ImageFile(
        filename="evidence.jpg",
        content_type="image/jpeg",
        size=2048,
        data="base64data=="
    )
    
    submission = IncidentSubmissionRequest(
        user_data=user_data,
        category=category,
        street=street,
        custom_text="Issue with evidence",
        extra_files=image_file
    )
    
    assert submission.extra_files == image_file

def test_api_response_model():
    """Test APIResponse model for SharePoint responses."""
    from app.models.response import APIResponse
    
    # Success response
    success_response = APIResponse(
        ResultCode=200,
        ErrorDescription="",
        ResultStatus="SUCCESS CREATE",
        data="TICKET-12345"
    )
    
    assert success_response.ResultCode == 200
    assert success_response.ErrorDescription == ""
    assert success_response.ResultStatus == "SUCCESS CREATE"
    assert success_response.data == "TICKET-12345"
    
    # Error response
    error_response = APIResponse(
        ResultCode=400,
        ErrorDescription="Invalid data",
        ResultStatus="ERROR",
        data=""
    )
    
    assert error_response.ResultCode == 400
    assert error_response.ErrorDescription == "Invalid data"

def test_api_payload_model():
    """Test APIPayload model for SharePoint integration."""
    from app.models.sharepoint import APIPayload
    
    payload = APIPayload(
        eventCallSourceId=4,
        cityCode="7400",
        cityDesc="נתניה",
        eventCallCenterId="3",
        eventCallDesc="Test complaint",
        streetCode="898",
        streetDesc="קרל פופר",
        houseNumber="123",
        callerFirstName="John",
        callerLastName="Doe",
        callerTZ="123456789",
        callerPhone1="0501234567",
        callerEmail="john@example.com",
        contactUsType="3"
    )
    
    # Check fixed municipality values
    assert payload.eventCallSourceId == 4
    assert payload.cityCode == "7400"
    assert payload.cityDesc == "נתניה"
    assert payload.eventCallCenterId == "3"
    assert payload.streetCode == "898"
    assert payload.streetDesc == "קרל פופר"
    assert payload.contactUsType == "3"
    
    # Check dynamic values
    assert payload.eventCallDesc == "Test complaint"
    assert payload.houseNumber == "123"
    assert payload.callerFirstName == "John"
    assert payload.callerLastName == "Doe"

def test_payload_transformation():
    """Test transformation from IncidentSubmissionRequest to APIPayload."""
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    from app.models.sharepoint import APIPayload
    
    # Create request
    user_data = UserData(
        first_name="Alice",
        last_name="Johnson",
        phone="0507654321",
        user_id="987654321",
        email="alice@example.com"
    )
    
    category = Category(
        id=2,
        name="Garbage Collection",
        text="Garbage issues",
        image_url="https://example.com/garbage.jpg",
        event_call_desc="Garbage collection problem"
    )
    
    street = StreetNumber(
        id=2,
        name="Oak Avenue",
        image_url="https://example.com/oak.jpg",
        house_number="456"
    )
    
    request = IncidentSubmissionRequest(
        user_data=user_data,
        category=category,
        street=street,
        custom_text="Garbage not collected for 3 days"
    )
    
    # Test manual transformation (transformation logic will be in service layer)
    payload = APIPayload(
        eventCallSourceId=4,  # Fixed
        cityCode="7400",  # Fixed
        cityDesc="נתניה",  # Fixed
        eventCallCenterId="3",  # Fixed
        eventCallDesc=request.custom_text or request.category.event_call_desc,
        streetCode="898",  # Fixed
        streetDesc="קרל פופר",  # Fixed
        houseNumber=request.street.house_number,
        callerFirstName=request.user_data.first_name,
        callerLastName=request.user_data.last_name,
        callerTZ=request.user_data.user_id or "",
        callerPhone1=request.user_data.phone,
        callerEmail=request.user_data.email or "",
        contactUsType="3"  # Fixed
    )
    
    assert payload.eventCallDesc == "Garbage not collected for 3 days"
    assert payload.houseNumber == "456"
    assert payload.callerFirstName == "Alice"
    assert payload.callerLastName == "Johnson"
    assert payload.callerTZ == "987654321"
    assert payload.callerPhone1 == "0507654321"
    assert payload.callerEmail == "alice@example.com"
