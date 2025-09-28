"""
Test payload transformation and formatting logic.
"""
import pytest
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_payload_transformer_import():
    """Test that payload transformer can be imported."""
    try:
        from app.services.payload_transformation import (
            PayloadTransformer, TransformationError, NetanyaMuniConfig
        )
        assert PayloadTransformer is not None
        assert TransformationError is not None
        assert NetanyaMuniConfig is not None
    except ImportError:
        pytest.fail("Could not import payload transformation service")

def test_netanya_muni_config_values():
    """Test NetanyaMuni fixed configuration values."""
    from app.services.payload_transformation import NetanyaMuniConfig
    
    config = NetanyaMuniConfig()
    
    # Verify fixed municipality values
    assert config.event_call_source_id == 4
    assert config.city_code == "7400"
    assert config.city_desc == "נתניה"
    assert config.event_call_center_id == "3"
    assert config.street_code == "898"
    assert config.street_desc == "קרל פופר"
    assert config.contact_us_type == "3"

def test_basic_incident_transformation():
    """Test basic incident request transformation to SharePoint format."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    from app.models.sharepoint import APIPayload
    
    transformer = PayloadTransformer()
    
    # Create test incident request
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="John",
            last_name="Doe",
            phone="0501234567",
            user_id="123456789",
            email="john@example.com"
        ),
        category=Category(
            id=1,
            name="Street Cleaning",
            text="Street cleaning issues",
            image_url="https://example.com/cleaning.jpg",
            event_call_desc="Street cleaning complaint"
        ),
        street=StreetNumber(
            id=1,
            name="Main Street",
            image_url="https://example.com/street.jpg",
            house_number="123"
        )
    )
    
    # Transform to SharePoint payload
    payload = transformer.transform_to_sharepoint(request)
    
    # Verify it's an APIPayload
    assert isinstance(payload, APIPayload)
    
    # Verify fixed municipality values
    assert payload.eventCallSourceId == 4
    assert payload.cityCode == "7400"
    assert payload.cityDesc == "נתניה"
    assert payload.eventCallCenterId == "3"
    assert payload.streetCode == "898"
    assert payload.streetDesc == "קרל פופר"
    assert payload.contactUsType == "3"
    
    # Verify mapped user data
    assert payload.callerFirstName == "John"
    assert payload.callerLastName == "Doe"
    assert payload.callerPhone1 == "0501234567"
    assert payload.callerTZ == "123456789"
    assert payload.callerEmail == "john@example.com"
    assert payload.houseNumber == "123"

def test_custom_text_priority_mapping():
    """Test that custom text takes priority over category description."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    # Create request with both custom text and category description
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Custom",
            last_name="User",
            phone="0507654321"
        ),
        category=Category(
            id=2,
            name="Garbage",
            text="Garbage collection",
            image_url="https://example.com/garbage.jpg",
            event_call_desc="Default garbage complaint"
        ),
        street=StreetNumber(
            id=2,
            name="Custom Street",
            image_url="https://example.com/custom.jpg",
            house_number="456"
        ),
        custom_text="Custom complaint text that should override category"
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Custom text should be used instead of category description
    assert payload.eventCallDesc == "Custom complaint text that should override category"

def test_category_description_fallback():
    """Test fallback to category description when no custom text."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    # Create request without custom text
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Fallback",
            last_name="User",
            phone="0509876543"
        ),
        category=Category(
            id=3,
            name="Parks",
            text="Parks maintenance",
            image_url="https://example.com/parks.jpg",
            event_call_desc="Park maintenance complaint"
        ),
        street=StreetNumber(
            id=3,
            name="Park Avenue",
            image_url="https://example.com/park_ave.jpg",
            house_number="789"
        )
        # No custom_text provided
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Should use category description as fallback
    assert payload.eventCallDesc == "Park maintenance complaint"

def test_optional_user_fields_handling():
    """Test handling of optional user data fields."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    # Create request with minimal user data (only required fields)
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Minimal",
            last_name="User",
            phone="0501111111"
            # No user_id or email
        ),
        category=Category(
            id=1,
            name="Test",
            text="Test category",
            image_url="https://example.com/test.jpg",
            event_call_desc="Test complaint"
        ),
        street=StreetNumber(
            id=1,
            name="Test Street",
            image_url="https://example.com/test_street.jpg",
            house_number="1"
        )
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Required fields should be present
    assert payload.callerFirstName == "Minimal"
    assert payload.callerLastName == "User"
    assert payload.callerPhone1 == "0501111111"
    
    # Optional fields should be empty strings
    assert payload.callerTZ == ""
    assert payload.callerEmail == ""

def test_hebrew_text_transformation():
    """Test transformation with Hebrew text content."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    # Create request with Hebrew content
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="יוחנן",
            last_name="כהן",
            phone="0508765432",
            user_id="987654321",
            email="yohanan@example.com"
        ),
        category=Category(
            id=4,
            name="ניקיון",
            text="בעיות ניקיון",
            image_url="https://example.com/cleaning_he.jpg",
            event_call_desc="תלונה על ניקיון רחובות"
        ),
        street=StreetNumber(
            id=4,
            name="רחוב הרצל",
            image_url="https://example.com/herzl.jpg",
            house_number="15א"
        ),
        custom_text="תלונה חמורה על פח זבל שבור ליד הבניין"
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Verify Hebrew text is preserved
    assert payload.callerFirstName == "יוחנן"
    assert payload.callerLastName == "כהן"
    assert payload.houseNumber == "15א"
    assert payload.eventCallDesc == "תלונה חמורה על פח זבל שבור ליד הבניין"
    
    # Fixed Hebrew values should remain
    assert payload.cityDesc == "נתניה"
    assert payload.streetDesc == "קרל פופר"

def test_empty_custom_text_handling():
    """Test handling of empty custom text (should fallback to category)."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Empty",
            last_name="Custom",
            phone="0502222222"
        ),
        category=Category(
            id=5,
            name="Traffic",
            text="Traffic issues",
            image_url="https://example.com/traffic.jpg",
            event_call_desc="Traffic light malfunction"
        ),
        street=StreetNumber(
            id=5,
            name="Traffic Street",
            image_url="https://example.com/traffic_street.jpg",
            house_number="999"
        ),
        custom_text=""  # Empty string
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Should fallback to category description when custom text is empty
    assert payload.eventCallDesc == "Traffic light malfunction"

def test_whitespace_custom_text_handling():
    """Test handling of whitespace-only custom text."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Whitespace",
            last_name="Test",
            phone="0503333333"
        ),
        category=Category(
            id=6,
            name="Utilities",
            text="Utility issues",
            image_url="https://example.com/utilities.jpg",
            event_call_desc="Water pipe leak"
        ),
        street=StreetNumber(
            id=6,
            name="Utility Street",
            image_url="https://example.com/utility_street.jpg",
            house_number="777"
        ),
        custom_text="   \t\n   "  # Whitespace only
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Should fallback to category description when custom text is whitespace only
    assert payload.eventCallDesc == "Water pipe leak"

def test_transformation_validation():
    """Test validation of transformation results."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Validation",
            last_name="Test",
            phone="0504444444"
        ),
        category=Category(
            id=7,
            name="Validation",
            text="Validation test",
            image_url="https://example.com/validation.jpg",
            event_call_desc="Validation test complaint"
        ),
        street=StreetNumber(
            id=7,
            name="Validation Street",
            image_url="https://example.com/validation_street.jpg",
            house_number="123"
        )
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Validate that all required fields are present and not empty
    assert payload.callerFirstName is not None and payload.callerFirstName != ""
    assert payload.callerLastName is not None and payload.callerLastName != ""
    assert payload.callerPhone1 is not None and payload.callerPhone1 != ""
    assert payload.eventCallDesc is not None and payload.eventCallDesc != ""
    assert payload.houseNumber is not None and payload.houseNumber != ""
    
    # Validate municipality fixed values
    assert payload.eventCallSourceId > 0
    assert payload.cityCode is not None and payload.cityCode != ""
    assert payload.cityDesc is not None and payload.cityDesc != ""

def test_transformation_error_handling():
    """Test error handling during transformation."""
    from app.services.payload_transformation import PayloadTransformer, TransformationError
    
    transformer = PayloadTransformer()
    
    # Test with None input
    with pytest.raises(TransformationError) as exc_info:
        transformer.transform_to_sharepoint(None)
    
    assert "request cannot be none" in str(exc_info.value).lower()

def test_long_text_field_handling():
    """Test handling of very long text fields."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    # Create very long custom text
    long_text = "Very long complaint text. " * 100  # ~2600 characters
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Long",
            last_name="Text",
            phone="0505555555"
        ),
        category=Category(
            id=8,
            name="Long Text",
            text="Long text test",
            image_url="https://example.com/long.jpg",
            event_call_desc="Short description"
        ),
        street=StreetNumber(
            id=8,
            name="Long Street",
            image_url="https://example.com/long_street.jpg",
            house_number="888"
        ),
        custom_text=long_text
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Should preserve the long text
    assert payload.eventCallDesc == long_text
    assert len(payload.eventCallDesc) > 2000

def test_special_characters_in_house_number():
    """Test handling of special characters in house number."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Special",
            last_name="Chars",
            phone="0506666666"
        ),
        category=Category(
            id=9,
            name="Special",
            text="Special characters test",
            image_url="https://example.com/special.jpg",
            event_call_desc="Special character test"
        ),
        street=StreetNumber(
            id=9,
            name="Special Street",
            image_url="https://example.com/special_street.jpg",
            house_number="12א/3-ב"  # Hebrew letters and special chars
        )
    )
    
    payload = transformer.transform_to_sharepoint(request)
    
    # Should preserve special characters in house number
    assert payload.houseNumber == "12א/3-ב"

def test_transformation_immutability():
    """Test that transformation doesn't modify the original request."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    original_request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Immutable",
            last_name="Test",
            phone="0507777777"
        ),
        category=Category(
            id=10,
            name="Immutable",
            text="Immutability test",
            image_url="https://example.com/immutable.jpg",
            event_call_desc="Immutability test complaint"
        ),
        street=StreetNumber(
            id=10,
            name="Immutable Street",
            image_url="https://example.com/immutable_street.jpg",
            house_number="100"
        )
    )
    
    # Store original values
    original_first_name = original_request.user_data.first_name
    original_phone = original_request.user_data.phone
    original_house_number = original_request.street.house_number
    
    # Transform
    payload = transformer.transform_to_sharepoint(original_request)
    
    # Verify original request is unchanged
    assert original_request.user_data.first_name == original_first_name
    assert original_request.user_data.phone == original_phone
    assert original_request.street.house_number == original_house_number
    
    # Verify transformation worked
    assert payload.callerFirstName == original_first_name
    assert payload.callerPhone1 == original_phone
    assert payload.houseNumber == original_house_number

def test_multiple_transformations_consistency():
    """Test that multiple transformations of the same request produce identical results."""
    from app.services.payload_transformation import PayloadTransformer
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    transformer = PayloadTransformer()
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Consistent",
            last_name="Test",
            phone="0508888888",
            user_id="111111111",
            email="consistent@example.com"
        ),
        category=Category(
            id=11,
            name="Consistency",
            text="Consistency test",
            image_url="https://example.com/consistency.jpg",
            event_call_desc="Consistency test complaint"
        ),
        street=StreetNumber(
            id=11,
            name="Consistent Street",
            image_url="https://example.com/consistent_street.jpg",
            house_number="200"
        ),
        custom_text="Consistent custom text"
    )
    
    # Transform multiple times
    payload1 = transformer.transform_to_sharepoint(request)
    payload2 = transformer.transform_to_sharepoint(request)
    payload3 = transformer.transform_to_sharepoint(request)
    
    # All transformations should be identical
    assert payload1.model_dump() == payload2.model_dump()
    assert payload2.model_dump() == payload3.model_dump()
    assert payload1.model_dump() == payload3.model_dump()
