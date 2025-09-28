"""
Integration tests for file validation service with real-world scenarios.
"""
import pytest
import base64
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_realistic_file_upload_workflow():
    """Test a realistic file upload workflow from request to multipart preparation."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Simulate a realistic JPEG upload
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
    fake_jpeg_data = jpeg_header + b'fake jpeg image content for testing' * 100
    base64_data = base64.b64encode(fake_jpeg_data).decode('utf-8')
    
    image_file = ImageFile(
        filename="incident_evidence_photo.jpg",
        content_type="image/jpeg",
        size=len(fake_jpeg_data),
        data=base64_data
    )
    
    # Step 1: Validate the file
    validation_result = service.validate_file(image_file)
    assert validation_result.is_valid is True
    assert len(validation_result.errors) == 0
    
    # Step 2: Prepare for multipart upload
    multipart_file = service.prepare_multipart_file(image_file)
    assert multipart_file.field_name == "attachment"
    assert multipart_file.filename == "incident_evidence_photo.jpg"
    assert multipart_file.content_type == "image/jpeg"
    assert multipart_file.data == fake_jpeg_data

def test_large_file_boundary_cases():
    """Test file size validation at exact boundaries."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test exactly at 10MB limit
    max_size = 10 * 1024 * 1024  # 10MB
    large_data = b'x' * max_size
    base64_data = base64.b64encode(large_data).decode('utf-8')
    
    large_image = ImageFile(
        filename="large_image.png",
        content_type="image/png",
        size=max_size,
        data=base64_data
    )
    
    validation_result = service.validate_file(large_image)
    assert validation_result.is_valid is True
    
    # Test 1 byte over limit
    oversized_data = b'x' * (max_size + 1)
    oversized_base64 = base64.b64encode(oversized_data).decode('utf-8')
    
    oversized_image = ImageFile(
        filename="oversized_image.png",
        content_type="image/png", 
        size=max_size + 1,
        data=oversized_base64
    )
    
    validation_result = service.validate_file(oversized_image)
    assert validation_result.is_valid is False
    assert any("size" in error.lower() for error in validation_result.errors)

def test_multiple_validation_errors():
    """Test that validation catches multiple errors in a single file."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # File with multiple problems: unsupported format, too large, invalid base64
    problematic_file = ImageFile(
        filename="bad_file.exe",
        content_type="application/x-executable",  # Unsupported format
        size=20 * 1024 * 1024,  # Too large (20MB)
        data="invalid_base64_data!@#$%"  # Invalid base64
    )
    
    validation_result = service.validate_file(problematic_file)
    assert validation_result.is_valid is False
    assert len(validation_result.errors) >= 2  # Should catch multiple errors
    
    # Check that all error types are caught
    error_text = " ".join(validation_result.errors).lower()
    assert "format" in error_text or "type" in error_text
    assert "size" in error_text

def test_webp_format_support():
    """Test specific support for WebP format (modern image format)."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Simulate WebP file
    webp_header = b'RIFF\x12\x34\x56\x78WEBP'
    fake_webp_data = webp_header + b'VP8 fake webp data' * 50
    base64_data = base64.b64encode(fake_webp_data).decode('utf-8')
    
    webp_image = ImageFile(
        filename="modern_image.webp",
        content_type="image/webp",
        size=len(fake_webp_data),
        data=base64_data
    )
    
    validation_result = service.validate_file(webp_image)
    assert validation_result.is_valid is True
    
    multipart_file = service.prepare_multipart_file(webp_image)
    assert multipart_file.content_type == "image/webp"

def test_gif_animated_support():
    """Test support for GIF format (potentially animated)."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Simulate GIF file
    gif_header = b'GIF89a'
    fake_gif_data = gif_header + b'fake gif animation data' * 100
    base64_data = base64.b64encode(fake_gif_data).decode('utf-8')
    
    gif_image = ImageFile(
        filename="animation.gif",
        content_type="image/gif",
        size=len(fake_gif_data),
        data=base64_data
    )
    
    validation_result = service.validate_file(gif_image)
    assert validation_result.is_valid is True

def test_edge_case_filenames():
    """Test edge cases for filenames."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    test_data = b'test image data'
    base64_data = base64.b64encode(test_data).decode('utf-8')
    
    edge_case_filenames = [
        "file with spaces.jpg",
        "file-with-dashes.png",
        "file_with_underscores.gif",
        "file.with.multiple.dots.webp",
        "תמונה_בעברית.jpg",  # Hebrew filename
        "файл_на_русском.png",  # Cyrillic filename
        "very_long_filename_that_might_cause_issues_in_some_systems_but_should_be_handled_gracefully.jpg"
    ]
    
    for filename in edge_case_filenames:
        image_file = ImageFile(
            filename=filename,
            content_type="image/jpeg",
            size=len(test_data),
            data=base64_data
        )
        
        validation_result = service.validate_file(image_file)
        assert validation_result.is_valid is True
        
        multipart_file = service.prepare_multipart_file(image_file)
        assert multipart_file.filename == filename

def test_base64_padding_variations():
    """Test various base64 padding scenarios."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test different data lengths that result in different padding
    test_data_variants = [
        b'a',      # Should result in padding ==
        b'ab',     # Should result in padding =
        b'abc',    # Should result in no padding
        b'abcd',   # Should result in no padding
    ]
    
    for test_data in test_data_variants:
        base64_data = base64.b64encode(test_data).decode('utf-8')
        
        image_file = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=len(test_data),
            data=base64_data
        )
        
        validation_result = service.validate_file(image_file)
        assert validation_result.is_valid is True

def test_error_message_quality():
    """Test that error messages are helpful and specific."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    
    service = FileValidationService()
    
    # Test unsupported format error message
    unsupported_file = ImageFile(
        filename="document.pdf",
        content_type="application/pdf",
        size=1024,
        data="dGVzdA=="  # valid base64
    )
    
    result = service.validate_file(unsupported_file)
    assert result.is_valid is False
    assert len(result.errors) > 0
    
    error_message = result.errors[0]
    assert "pdf" in error_message.lower() or "application/pdf" in error_message
    assert "supported formats" in error_message.lower()
    
    # Test file size error message
    large_file = ImageFile(
        filename="huge.jpg",
        content_type="image/jpeg",
        size=50 * 1024 * 1024,  # 50MB
        data="dGVzdA=="
    )
    
    result = service.validate_file(large_file)
    assert result.is_valid is False
    error_message = result.errors[0]
    assert "size" in error_message.lower()
    assert "10" in error_message  # Should mention the 10MB limit

def test_concurrent_validations():
    """Test that the service can handle multiple concurrent validations."""
    from app.services.file_validation import FileValidationService
    from app.models.request import ImageFile
    import concurrent.futures
    
    def validate_file(service, file_index):
        test_data = f'test image data {file_index}'.encode()
        base64_data = base64.b64encode(test_data).decode('utf-8')
        
        image_file = ImageFile(
            filename=f"test_{file_index}.jpg",
            content_type="image/jpeg",
            size=len(test_data),
            data=base64_data
        )
        
        return service.validate_file(image_file)
    
    service = FileValidationService()
    
    # Test concurrent validations
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(validate_file, service, i) 
            for i in range(10)
        ]
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # All should be valid
    assert len(results) == 10
    assert all(result.is_valid for result in results)
