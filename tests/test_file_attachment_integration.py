"""
Test integrated file attachment handling in SharePoint requests.
"""
import pytest
import base64
from unittest.mock import patch, Mock
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_incident_service_import():
    """Test that integrated incident service can be imported."""
    try:
        from app.services.incident_service import (
            IncidentService, IncidentSubmissionError, SubmissionResult
        )
        assert IncidentService is not None
        assert IncidentSubmissionError is not None
        assert SubmissionResult is not None
    except ImportError:
        pytest.fail("Could not import incident service")

def test_incident_service_initialization():
    """Test incident service initialization with all dependencies."""
    from app.services.incident_service import IncidentService
    
    service = IncidentService()
    
    # Should have all required dependencies
    assert service.payload_transformer is not None
    assert service.file_service is not None
    assert service.sharepoint_client is not None
    assert service.error_service is not None

def test_submit_incident_without_file():
    """Test submitting incident without file attachment."""
    from app.services.incident_service import IncidentService
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber
    
    service = IncidentService()
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="NoFile",
            last_name="Test",
            phone="0501234567",
            user_id="123456789",
            email="nofile@example.com"
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
            name="Test Street",
            image_url="https://example.com/street.jpg",
            house_number="123"
        ),
        custom_text="Test incident without file attachment"
    )
    
    # Mock SharePoint response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "TICKET-NO-FILE-123"
    }
    
    with patch.object(service.sharepoint_client.session, 'post', return_value=mock_response):
        result = service.submit_incident(request)
        
        assert result.success is True
        assert result.ticket_id == "TICKET-NO-FILE-123"
        assert result.has_file is False
        assert "correlation_id" in result.metadata

def test_submit_incident_with_valid_file():
    """Test submitting incident with valid file attachment."""
    from app.services.incident_service import IncidentService
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    
    service = IncidentService()
    
    # Create valid image file
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # JPEG header
    base64_data = base64.b64encode(test_image_data).decode('utf-8')
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="WithFile",
            last_name="Test",
            phone="0507654321",
            user_id="987654321",
            email="withfile@example.com"
        ),
        category=Category(
            id=2,
            name="Graffiti",
            text="Graffiti removal",
            image_url="https://example.com/graffiti.jpg",
            event_call_desc="Graffiti complaint"
        ),
        street=StreetNumber(
            id=2,
            name="Graffiti Street",
            image_url="https://example.com/graffiti_street.jpg",
            house_number="456"
        ),
        custom_text="Test incident with image evidence",
        extra_files=ImageFile(
            filename="evidence.jpg",
            content_type="image/jpeg",
            size=len(test_image_data),
            data=base64_data
        )
    )
    
    # Mock SharePoint response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "TICKET-WITH-FILE-456"
    }
    
    with patch.object(service.sharepoint_client.session, 'post', return_value=mock_response):
        result = service.submit_incident(request)
        
        assert result.success is True
        assert result.ticket_id == "TICKET-WITH-FILE-456"
        assert result.has_file is True
        assert result.file_info["filename"] == "evidence.jpg"
        assert result.file_info["content_type"] == "image/jpeg"

def test_submit_incident_with_invalid_file():
    """Test submitting incident with invalid file attachment."""
    from app.services.incident_service import IncidentService, IncidentSubmissionError
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    
    service = IncidentService()
    
    # Create invalid image file (wrong format)
    invalid_data = b"This is not image data"
    base64_data = base64.b64encode(invalid_data).decode('utf-8')
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="InvalidFile",
            last_name="Test",
            phone="0509876543"
        ),
        category=Category(
            id=3,
            name="Invalid Test",
            text="Invalid file test",
            image_url="https://example.com/invalid.jpg",
            event_call_desc="Invalid file test"
        ),
        street=StreetNumber(
            id=3,
            name="Invalid Street",
            image_url="https://example.com/invalid_street.jpg",
            house_number="789"
        ),
        extra_files=ImageFile(
            filename="invalid.exe",
            content_type="application/x-executable",
            size=len(invalid_data),
            data=base64_data
        )
    )
    
    with pytest.raises(IncidentSubmissionError) as exc_info:
        service.submit_incident(request)
    
    assert "file validation" in str(exc_info.value).lower()

def test_file_validation_integration():
    """Test file validation integration in incident submission."""
    from app.services.incident_service import IncidentService
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    
    service = IncidentService()
    
    # Test various file formats
    test_cases = [
        # Valid JPEG
        {
            "data": b'\xff\xd8\xff\xe0\x00\x10JFIF',
            "filename": "valid.jpg",
            "content_type": "image/jpeg",
            "should_pass": True
        },
        # Valid PNG
        {
            "data": b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR',
            "filename": "valid.png", 
            "content_type": "image/png",
            "should_pass": True
        },
        # Invalid file (too large)
        {
            "data": b"X" * (11 * 1024 * 1024),  # 11MB - too large
            "filename": "toolarge.jpg",
            "content_type": "image/jpeg",
            "should_pass": False
        },
        # Invalid content type
        {
            "data": b"PDF content",
            "filename": "document.pdf",
            "content_type": "application/pdf",
            "should_pass": False
        }
    ]
    
    for i, case in enumerate(test_cases):
        base64_data = base64.b64encode(case["data"]).decode('utf-8')
        
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name=f"FileTest{i}",
                last_name="User",
                phone=f"05011111{i}{i}"
            ),
            category=Category(
                id=i,
                name=f"FileTest{i}",
                text=f"File test {i}",
                image_url=f"https://example.com/test{i}.jpg",
                event_call_desc=f"File test {i}"
            ),
            street=StreetNumber(
                id=i,
                name=f"Test Street {i}",
                image_url=f"https://example.com/street{i}.jpg",
                house_number=str(i * 100)
            ),
            extra_files=ImageFile(
                filename=case["filename"],
                content_type=case["content_type"],
                size=len(case["data"]),
                data=base64_data
            )
        )
        
        if case["should_pass"]:
            # Mock successful SharePoint response for valid files
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ResultCode": 200,
                "ErrorDescription": "",
                "ResultStatus": "SUCCESS CREATE",
                "data": f"TICKET-VALID-{i}"
            }
            
            with patch.object(service.sharepoint_client.session, 'post', return_value=mock_response):
                result = service.submit_incident(request)
                assert result.success is True
        else:
            # Should raise validation error for invalid files
            with pytest.raises(Exception):
                service.submit_incident(request)

def test_multipart_content_disposition_headers():
    """Test proper Content-Disposition headers in multipart requests."""
    from app.services.incident_service import IncidentService
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    
    service = IncidentService()
    
    # Create request with file
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    base64_data = base64.b64encode(test_image_data).decode('utf-8')
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Headers",
            last_name="Test",
            phone="0508765432"
        ),
        category=Category(
            id=1,
            name="Headers Test",
            text="Content-Disposition test",
            image_url="https://example.com/headers.jpg",
            event_call_desc="Headers test"
        ),
        street=StreetNumber(
            id=1,
            name="Headers Street",
            image_url="https://example.com/headers_street.jpg",
            house_number="HEADERS"
        ),
        extra_files=ImageFile(
            filename="test_headers.jpg",
            content_type="image/jpeg",
            size=len(test_image_data),
            data=base64_data
        )
    )
    
    # Mock response and capture request details
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "TICKET-HEADERS-TEST"
    }
    
    with patch.object(service.sharepoint_client.session, 'post', return_value=mock_response) as mock_post:
        result = service.submit_incident(request)
        
        # Verify request was made
        mock_post.assert_called_once()
        
        # Check that multipart body contains proper headers
        call_kwargs = mock_post.call_args[1]
        body_data = call_kwargs["data"]
        body_str = body_data.decode('utf-8', errors='ignore')
        
        # Should contain proper Content-Disposition headers
        assert 'Content-Disposition: form-data; name="json"' in body_str
        assert 'Content-Disposition: form-data; name="attachment"; filename="test_headers.jpg"' in body_str
        assert 'Content-Type: image/jpeg' in body_str

def test_hebrew_filename_handling():
    """Test handling of Hebrew filenames in file attachments."""
    from app.services.incident_service import IncidentService
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    
    service = IncidentService()
    
    # Create request with Hebrew filename
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    base64_data = base64.b64encode(test_image_data).decode('utf-8')
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Hebrew",
            last_name="Test",
            phone="0509999999"
        ),
        category=Category(
            id=1,
            name="Hebrew File Test",
            text="Hebrew filename test",
            image_url="https://example.com/hebrew.jpg",
            event_call_desc="Hebrew filename test"
        ),
        street=StreetNumber(
            id=1,
            name="Hebrew Street",
            image_url="https://example.com/hebrew_street.jpg",
            house_number="עברית"
        ),
        extra_files=ImageFile(
            filename="תמונת_ראיות.jpg",  # Hebrew filename
            content_type="image/jpeg",
            size=len(test_image_data),
            data=base64_data
        )
    )
    
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "TICKET-HEBREW-FILE"
    }
    
    with patch.object(service.sharepoint_client.session, 'post', return_value=mock_response):
        result = service.submit_incident(request)
        
        assert result.success is True
        assert result.file_info["filename"] == "תמונת_ראיות.jpg"

def test_submission_result_structure():
    """Test submission result data structure."""
    from app.services.incident_service import SubmissionResult
    
    # Test without file
    result_no_file = SubmissionResult(
        success=True,
        ticket_id="TEST-123",
        correlation_id="corr-123",
        has_file=False,
        file_info=None,
        metadata={"test": "data"}
    )
    
    assert result_no_file.success is True
    assert result_no_file.ticket_id == "TEST-123"
    assert result_no_file.has_file is False
    assert result_no_file.file_info is None
    
    # Test with file
    file_info = {
        "filename": "test.jpg",
        "content_type": "image/jpeg",
        "size": 12345
    }
    
    result_with_file = SubmissionResult(
        success=True,
        ticket_id="TEST-456",
        correlation_id="corr-456",
        has_file=True,
        file_info=file_info,
        metadata={"file_processed": True}
    )
    
    assert result_with_file.success is True
    assert result_with_file.has_file is True
    assert result_with_file.file_info["filename"] == "test.jpg"

def test_sharepoint_error_handling_with_file():
    """Test SharePoint error handling when file is involved."""
    from app.services.incident_service import IncidentService, IncidentSubmissionError
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    
    service = IncidentService()
    
    # Create request with file
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    base64_data = base64.b64encode(test_image_data).decode('utf-8')
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Error",
            last_name="Test",
            phone="0506666666"
        ),
        category=Category(
            id=1,
            name="Error Test",
            text="Error test category",
            image_url="https://example.com/error.jpg",
            event_call_desc="Error test"
        ),
        street=StreetNumber(
            id=1,
            name="Error Street",
            image_url="https://example.com/error_street.jpg",
            house_number="ERROR"
        ),
        extra_files=ImageFile(
            filename="error_test.jpg",
            content_type="image/jpeg",
            size=len(test_image_data),
            data=base64_data
        )
    )
    
    # Mock SharePoint error response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 400,
        "ErrorDescription": "File attachment failed",
        "ResultStatus": "ERROR",
        "data": ""
    }
    
    with patch.object(service.sharepoint_client.session, 'post', return_value=mock_response):
        with pytest.raises(IncidentSubmissionError) as exc_info:
            service.submit_incident(request)
        
        assert "sharepoint" in str(exc_info.value).lower()
        assert "file attachment failed" in str(exc_info.value).lower()

def test_large_file_handling():
    """Test handling of files near the size limit."""
    from app.services.incident_service import IncidentService
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    
    service = IncidentService()
    
    # Create file just under the 10MB limit
    large_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + (b'X' * (9 * 1024 * 1024))  # ~9MB
    base64_data = base64.b64encode(large_image_data).decode('utf-8')
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Large",
            last_name="File",
            phone="0507777777"
        ),
        category=Category(
            id=1,
            name="Large File Test",
            text="Large file test",
            image_url="https://example.com/large.jpg",
            event_call_desc="Large file test"
        ),
        street=StreetNumber(
            id=1,
            name="Large Street",
            image_url="https://example.com/large_street.jpg",
            house_number="LARGE"
        ),
        extra_files=ImageFile(
            filename="large_file.jpg",
            content_type="image/jpeg",
            size=len(large_image_data),
            data=base64_data
        )
    )
    
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE",
        "data": "TICKET-LARGE-FILE"
    }
    
    with patch.object(service.sharepoint_client.session, 'post', return_value=mock_response):
        result = service.submit_incident(request)
        
        assert result.success is True
        assert result.file_info["size"] > 9 * 1024 * 1024  # Should be large

def test_correlation_id_propagation():
    """Test correlation ID propagation through file handling workflow."""
    from app.services.incident_service import IncidentService
    from app.models.request import IncidentSubmissionRequest, UserData, Category, StreetNumber, ImageFile
    
    service = IncidentService()
    
    # Create request with file
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    base64_data = base64.b64encode(test_image_data).decode('utf-8')
    
    request = IncidentSubmissionRequest(
        user_data=UserData(
            first_name="Correlation",
            last_name="Test",
            phone="0508888888"
        ),
        category=Category(
            id=1,
            name="Correlation Test",
            text="Correlation ID test",
            image_url="https://example.com/correlation.jpg",
            event_call_desc="Correlation test"
        ),
        street=StreetNumber(
            id=1,
            name="Correlation Street",
            image_url="https://example.com/correlation_street.jpg",
            house_number="CORR"
        ),
        extra_files=ImageFile(
            filename="correlation_test.jpg",
            content_type="image/jpeg",
            size=len(test_image_data),
            data=base64_data
        )
    )
    
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ResultCode": 200,
        "ErrorDescription": "",
        "ResultStatus": "SUCCESS CREATE", 
        "data": "TICKET-CORRELATION"
    }
    
    with patch.object(service.sharepoint_client.session, 'post', return_value=mock_response):
        result = service.submit_incident(request)
        
        # Should have correlation ID in result
        assert "correlation_id" in result.metadata
        correlation_id = result.metadata["correlation_id"]
        assert correlation_id is not None
        assert len(correlation_id) > 0
        
        # Should be valid UUID format
        import uuid
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Invalid correlation ID format: {correlation_id}")
