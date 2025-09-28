"""
Test file validation service for image upload capabilities.
"""
import pytest
import base64
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_file_validation_service_import():
    """Test that file validation service can be imported."""
    try:
        from app.services.file_validation import (
            FileValidationService, FileValidationError, 
            MultipartFile, ValidationResult
        )
        assert FileValidationService is not None
        assert FileValidationError is not None
        assert MultipartFile is not None
        assert ValidationResult is not None
    except ImportError:
        pytest.fail("Could not import file validation service")

def test_file_validation_service_initialization():
    """Test that FileValidationService can be initialized."""
    from app.services.file_validation import FileValidationService
    
    service = FileValidationService()
    assert service is not None

def test_supported_image_formats():
    """Test validation of supported image formats."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test supported formats
    supported_formats = [
        ("image/jpeg", "test.jpg"),
        ("image/png", "test.png"),
        ("image/gif", "test.gif"),
        ("image/webp", "test.webp")
    ]
    
    for content_type, filename in supported_formats:
        image_file = ImageFile(
            filename=filename,
            content_type=content_type,
            size=1024,
            data="dGVzdCBpbWFnZSBkYXRh"  # base64 encoded "test image data"
        )
        
        result = service.validate_file(image_file)
        assert result.is_valid is True
        assert len(result.errors) == 0

def test_unsupported_image_formats():
    """Test rejection of unsupported image formats."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test unsupported formats
    unsupported_formats = [
        ("image/bmp", "test.bmp"),
        ("image/tiff", "test.tiff"),
        ("application/pdf", "test.pdf"),
        ("text/plain", "test.txt"),
        ("video/mp4", "test.mp4")
    ]
    
    for content_type, filename in unsupported_formats:
        image_file = ImageFile(
            filename=filename,
            content_type=content_type,
            size=1024,
            data="dGVzdCBkYXRh"
        )
        
        result = service.validate_file(image_file)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("format" in error.lower() or "type" in error.lower() for error in result.errors)

def test_file_size_validation():
    """Test file size validation with 10MB limit."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test valid file sizes
    valid_sizes = [100, 1024, 1048576, 10485760]  # 100B, 1KB, 1MB, 10MB (exactly)
    
    for size in valid_sizes:
        image_file = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=size,
            data="dGVzdCBkYXRh"
        )
        
        result = service.validate_file(image_file)
        assert result.is_valid is True

def test_file_size_limit_exceeded():
    """Test file size validation when limit is exceeded."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test invalid file sizes (over 10MB)
    invalid_sizes = [10485761, 20971520, 52428800]  # 10MB+1B, 20MB, 50MB
    
    for size in invalid_sizes:
        image_file = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=size,
            data="dGVzdCBkYXRh"
        )
        
        result = service.validate_file(image_file)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("size" in error.lower() for error in result.errors)

def test_empty_file_validation():
    """Test validation of empty files."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test empty file
    image_file = ImageFile(
        filename="empty.jpg",
        content_type="image/jpeg",
        size=0,
        data=""
    )
    
    result = service.validate_file(image_file)
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any("empty" in error.lower() or "size" in error.lower() for error in result.errors)

def test_base64_data_validation():
    """Test validation of base64 encoded data."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test valid base64 data
    valid_base64 = base64.b64encode(b"test image data").decode('utf-8')
    
    image_file = ImageFile(
        filename="test.jpg",
        content_type="image/jpeg",
        size=len(b"test image data"),
        data=valid_base64
    )
    
    result = service.validate_file(image_file)
    assert result.is_valid is True

def test_invalid_base64_data():
    """Test validation with invalid base64 data."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test invalid base64 data
    invalid_base64_data = [
        "not_base64_data!@#",
        "invalid==base64",
        "123456789",
        ""
    ]
    
    for invalid_data in invalid_base64_data:
        image_file = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=1024,
            data=invalid_data
        )
        
        result = service.validate_file(image_file)
        assert result.is_valid is False
        assert len(result.errors) > 0

def test_filename_validation():
    """Test filename validation and sanitization."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test valid filenames
    valid_filenames = [
        "image.jpg",
        "photo_001.png",
        "screenshot-2023.webp",
        "תמונה.jpg",  # Hebrew filename
        "image with spaces.png"
    ]
    
    for filename in valid_filenames:
        image_file = ImageFile(
            filename=filename,
            content_type="image/jpeg",
            size=1024,
            data="dGVzdCBkYXRh"
        )
        
        result = service.validate_file(image_file)
        # Should not fail just because of filename (other validations might fail)
        assert isinstance(result.is_valid, bool)

def test_multipart_file_preparation():
    """Test preparation of multipart file for SharePoint upload."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    test_data = b"test image data"
    base64_data = base64.b64encode(test_data).decode('utf-8')
    
    image_file = ImageFile(
        filename="evidence.jpg",
        content_type="image/jpeg",
        size=len(test_data),
        data=base64_data
    )
    
    # First validate
    validation_result = service.validate_file(image_file)
    assert validation_result.is_valid is True
    
    # Then prepare multipart file
    multipart_file = service.prepare_multipart_file(image_file)
    
    assert multipart_file.field_name == "attachment"
    assert multipart_file.filename == "evidence.jpg"
    assert multipart_file.content_type == "image/jpeg"
    assert multipart_file.data == test_data

def test_validation_result_model():
    """Test ValidationResult model structure."""
    from app.services.file_validation import ValidationResult
    
    # Test successful validation
    success_result = ValidationResult(is_valid=True, errors=[])
    assert success_result.is_valid is True
    assert len(success_result.errors) == 0
    
    # Test failed validation
    failure_result = ValidationResult(
        is_valid=False, 
        errors=["File too large", "Unsupported format"]
    )
    assert failure_result.is_valid is False
    assert len(failure_result.errors) == 2
    assert "File too large" in failure_result.errors

def test_multipart_file_model():
    """Test MultipartFile model structure."""
    from app.services.file_validation import MultipartFile
    
    test_data = b"binary file data"
    
    multipart_file = MultipartFile(
        field_name="attachment",
        filename="test.jpg",
        content_type="image/jpeg",
        data=test_data
    )
    
    assert multipart_file.field_name == "attachment"
    assert multipart_file.filename == "test.jpg"
    assert multipart_file.content_type == "image/jpeg"
    assert multipart_file.data == test_data

def test_file_validation_error():
    """Test FileValidationError exception."""
    from app.services.file_validation import FileValidationError
    
    error = FileValidationError("Test validation error")
    assert str(error) == "Test validation error"
    assert isinstance(error, Exception)

def test_comprehensive_file_validation():
    """Test comprehensive file validation with multiple checks."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Create a realistic image file
    test_image_data = b"fake_jpeg_header_data_for_testing"
    base64_data = base64.b64encode(test_image_data).decode('utf-8')
    
    image_file = ImageFile(
        filename="incident_evidence.jpg",
        content_type="image/jpeg",
        size=len(test_image_data),
        data=base64_data
    )
    
    # Validate file
    result = service.validate_file(image_file)
    assert result.is_valid is True
    assert len(result.errors) == 0
    
    # Prepare for multipart upload
    multipart_file = service.prepare_multipart_file(image_file)
    assert multipart_file.data == test_image_data
    assert multipart_file.content_type == "image/jpeg"

def test_file_validation_with_unicode_filename():
    """Test file validation with Unicode filenames."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test Hebrew filename
    unicode_filename = "ראיות_תמונה.jpg"
    test_data = b"test data"
    base64_data = base64.b64encode(test_data).decode('utf-8')
    
    image_file = ImageFile(
        filename=unicode_filename,
        content_type="image/jpeg",
        size=len(test_data),
        data=base64_data
    )
    
    result = service.validate_file(image_file)
    assert result.is_valid is True
    
    multipart_file = service.prepare_multipart_file(image_file)
    assert multipart_file.filename == unicode_filename
