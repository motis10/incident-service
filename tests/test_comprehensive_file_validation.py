"""
Comprehensive tests for file validation with various image formats and sizes.
"""
import pytest
from pathlib import Path
import sys
import base64
import io
from unittest.mock import patch, MagicMock

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.services.file_validation import FileValidationService, FileValidationError
from app.models.request import ImageFile


class TestFileFormatValidation:
    """Test file format validation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidationService()
    
    def test_valid_jpeg_file(self):
        """Test valid JPEG file validation."""
        # JPEG file header
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        image_file = ImageFile(
            filename="test.jpg",
            content_type="image/jpeg",
            size=len(jpeg_data),
            data=jpeg_data
        )
        
        result = self.validator.validate_file(image_file)
        assert result.is_valid is True
        assert result.file_type == "JPEG"
    
    def test_valid_png_file(self):
        """Test valid PNG file validation."""
        # PNG file header
        png_header = b'\x89PNG\r\n\x1a\n'
        png_data = png_header + b'\x00' * 100
        
        image_file = ImageFile(
            filename="test.png",
            content_type="image/png",
            size=len(png_data),
            data=png_data
        )
        
        result = self.validator.validate_file(image_file)
        assert result.is_valid is True
        assert result.file_type == "PNG"
    
    def test_valid_gif_file(self):
        """Test valid GIF file validation."""
        # GIF file header
        gif_header = b'GIF87a'
        gif_data = gif_header + b'\x00' * 100
        
        image_file = ImageFile(
            filename="test.gif",
            content_type="image/gif",
            size=len(gif_data),
            data=gif_data
        )
        
        result = self.validator.validate_file(image_file)
        assert result.is_valid is True
        assert result.file_type == "GIF"
    
    def test_valid_webp_file(self):
        """Test valid WebP file validation."""
        # WebP file header
        webp_header = b'RIFF\x00\x00\x00\x00WEBP'
        webp_data = webp_header + b'\x00' * 100
        
        image_file = ImageFile(
            filename="test.webp",
            content_type="image/webp",
            size=len(webp_data),
            data=webp_data
        )
        
        result = self.validator.validate_file(image_file)
        assert result.is_valid is True
        assert result.file_type == "WebP"
    
    def test_invalid_file_signature(self):
        """Test file with invalid signature."""
        # Text file disguised as image
        fake_image_data = b'This is not an image file'
        
        image_file = ImageFile(
            filename="fake.jpg",
            content_type="image/jpeg",
            size=len(fake_image_data),
            data=fake_image_data
        )
        
        with pytest.raises(FileValidationError, match="Invalid file signature"):
            self.validator.validate_file(image_file)
    
    def test_content_type_mismatch(self):
        """Test content type doesn't match file signature."""
        # PNG data with JPEG content type
        png_header = b'\x89PNG\r\n\x1a\n'
        png_data = png_header + b'\x00' * 100
        
        image_file = ImageFile(
            filename="test.png",
            content_type="image/jpeg",  # Wrong content type
            size=len(png_data),
            data=png_data
        )
        
        with pytest.raises(FileValidationError, match="Content type mismatch"):
            self.validator.validate_file(image_file)
    
    def test_executable_file_rejection(self):
        """Test executable files are rejected."""
        # EXE file header
        exe_header = b'MZ\x90\x00'
        exe_data = exe_header + b'\x00' * 100
        
        image_file = ImageFile(
            filename="virus.jpg",  # Disguised as image
            content_type="image/jpeg",
            size=len(exe_data),
            data=exe_data
        )
        
        with pytest.raises(FileValidationError, match="Invalid file signature"):
            self.validator.validate_file(image_file)


class TestFileSizeValidation:
    """Test file size validation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidationService()
    
    def test_maximum_file_size(self):
        """Test file at maximum allowed size."""
        # Create 5MB file (exactly at limit)
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        large_data = jpeg_header + b'\x00' * (5 * 1024 * 1024 - len(jpeg_header))
        
        image_file = ImageFile(
            filename="large.jpg",
            content_type="image/jpeg",
            size=len(large_data),
            data=large_data
        )
        
        result = self.validator.validate_file(image_file)
        assert result.is_valid is True
    
    def test_oversized_file_rejection(self):
        """Test oversized file is rejected."""
        # Create file larger than 5MB
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        oversized_data = jpeg_header + b'\x00' * (6 * 1024 * 1024)
        
        image_file = ImageFile(
            filename="oversized.jpg",
            content_type="image/jpeg",
            size=len(oversized_data),
            data=oversized_data
        )
        
        with pytest.raises(FileValidationError, match="File size exceeds"):
            self.validator.validate_file(image_file)
    
    def test_empty_file_rejection(self):
        """Test empty file is rejected."""
        image_file = ImageFile(
            filename="empty.jpg",
            content_type="image/jpeg",
            size=0,
            data=b''
        )
        
        with pytest.raises(FileValidationError, match="File is empty"):
            self.validator.validate_file(image_file)
    
    def test_minimum_file_size(self):
        """Test very small but valid file."""
        # Minimal JPEG header
        minimal_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9'
        
        image_file = ImageFile(
            filename="minimal.jpg",
            content_type="image/jpeg",
            size=len(minimal_jpeg),
            data=minimal_jpeg
        )
        
        result = self.validator.validate_file(image_file)
        assert result.is_valid is True


class TestFilenameValidation:
    """Test filename validation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidationService()
    
    def test_valid_filenames(self):
        """Test various valid filename formats."""
        valid_filenames = [
            "image.jpg",
            "photo.jpeg",
            "picture.png",
            "animation.gif",
            "modern.webp",
            "תמונה.jpg",  # Hebrew filename
            "תמונה_חדשה.png",  # Hebrew with underscore
            "image-2025.jpg",  # With dash and numbers
            "IMG_20250101_123456.jpg",  # Camera style
        ]
        
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        for filename in valid_filenames:
            image_file = ImageFile(
                filename=filename,
                content_type="image/jpeg",
                size=len(jpeg_data),
                data=jpeg_data
            )
            
            result = self.validator.validate_file(image_file)
            assert result.is_valid is True, f"Failed for filename: {filename}"
    
    def test_invalid_filenames(self):
        """Test invalid filename formats."""
        invalid_filenames = [
            "",                    # Empty
            "file.txt",           # Wrong extension
            "file.exe",           # Executable
            "file",               # No extension
            "../../../etc/passwd.jpg",  # Path traversal
            "con.jpg",            # Windows reserved name
            "prn.png",            # Windows reserved name
            "file\x00.jpg",       # Null character
            "file\n.jpg",         # Newline character
        ]
        
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        for filename in invalid_filenames:
            with pytest.raises(FileValidationError):
                image_file = ImageFile(
                    filename=filename,
                    content_type="image/jpeg",
                    size=len(jpeg_data),
                    data=jpeg_data
                )
                self.validator.validate_file(image_file)
    
    def test_long_filename_validation(self):
        """Test very long filename validation."""
        # 256 character filename (should be rejected)
        long_filename = "a" * 250 + ".jpg"
        
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        with pytest.raises(FileValidationError, match="Filename too long"):
            image_file = ImageFile(
                filename=long_filename,
                content_type="image/jpeg",
                size=len(jpeg_data),
                data=jpeg_data
            )
            self.validator.validate_file(image_file)


class TestBase64Validation:
    """Test base64 encoding and validation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidationService()
    
    def test_valid_base64_encoding(self):
        """Test valid base64 encoded data."""
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        base64_data = base64.b64encode(jpeg_data).decode('utf-8')
        
        result = self.validator.validate_base64(base64_data)
        assert result.is_valid is True
        assert result.decoded_data == jpeg_data
    
    def test_invalid_base64_encoding(self):
        """Test invalid base64 data."""
        invalid_base64_strings = [
            "This is not base64!",
            "SGVsbG8gV29ybGQ=!",  # Invalid character
            "SGVsbG8=V29ybGQ=",   # Invalid padding
            "",                   # Empty
            "A",                  # Too short
        ]
        
        for invalid_data in invalid_base64_strings:
            with pytest.raises(FileValidationError, match="Invalid base64"):
                self.validator.validate_base64(invalid_data)
    
    def test_base64_padding_variations(self):
        """Test different base64 padding scenarios."""
        test_data = b"Hello World"
        
        # Test various valid padding scenarios
        base64_data = base64.b64encode(test_data).decode('utf-8')
        result = self.validator.validate_base64(base64_data)
        assert result.is_valid is True
        assert result.decoded_data == test_data
    
    def test_base64_with_whitespace(self):
        """Test base64 data with whitespace (should be handled)."""
        test_data = b"Test data"
        base64_data = base64.b64encode(test_data).decode('utf-8')
        
        # Add whitespace
        base64_with_whitespace = f"  {base64_data}  \n"
        
        result = self.validator.validate_base64(base64_with_whitespace)
        assert result.is_valid is True
        assert result.decoded_data == test_data


class TestMaliciousFileDetection:
    """Test detection of malicious or dangerous files."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidationService()
    
    def test_script_injection_detection(self):
        """Test detection of script content in images."""
        # Image with embedded script
        malicious_content = b'\xff\xd8\xff\xe0\x00\x10JFIF<script>alert("xss")</script>'
        
        image_file = ImageFile(
            filename="malicious.jpg",
            content_type="image/jpeg",
            size=len(malicious_content),
            data=malicious_content
        )
        
        with pytest.raises(FileValidationError, match="Suspicious content detected"):
            self.validator.validate_file(image_file)
    
    def test_polyglot_file_detection(self):
        """Test detection of polyglot files (valid as multiple formats)."""
        # File that could be both image and HTML
        polyglot_content = b'\xff\xd8\xff\xe0\x00\x10JFIF<!--<html><body>test</body></html>-->'
        
        image_file = ImageFile(
            filename="polyglot.jpg",
            content_type="image/jpeg",
            size=len(polyglot_content),
            data=polyglot_content
        )
        
        with pytest.raises(FileValidationError, match="Suspicious content detected"):
            self.validator.validate_file(image_file)
    
    def test_metadata_size_validation(self):
        """Test validation of image metadata size."""
        # JPEG with excessively large metadata section
        jpeg_header = b'\xff\xd8\xff\xe1\xff\xff'  # Large metadata marker
        large_metadata = b'\x00' * (100 * 1024)  # 100KB metadata
        jpeg_data = jpeg_header + large_metadata + b'\xff\xd9'
        
        image_file = ImageFile(
            filename="large_metadata.jpg",
            content_type="image/jpeg",
            size=len(jpeg_data),
            data=jpeg_data
        )
        
        with pytest.raises(FileValidationError, match="Suspicious content detected"):
            self.validator.validate_file(image_file)


class TestFileValidationIntegration:
    """Test file validation integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidationService()
    
    def test_complete_validation_workflow(self):
        """Test complete file validation workflow."""
        # Valid JPEG image
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 1000 + b'\xff\xd9'
        
        image_file = ImageFile(
            filename="complete_test.jpg",
            content_type="image/jpeg",
            size=len(jpeg_data),
            data=jpeg_data
        )
        
        result = self.validator.validate_file(image_file)
        
        assert result.is_valid is True
        assert result.file_type == "JPEG"
        assert result.file_size == len(jpeg_data)
        assert result.filename == "complete_test.jpg"
        assert result.validation_errors == []
    
    def test_validation_with_multiple_errors(self):
        """Test validation that encounters multiple errors."""
        # File with multiple issues
        invalid_data = b'Not an image'
        
        image_file = ImageFile(
            filename="",  # Invalid filename
            content_type="text/plain",  # Invalid content type
            size=0,  # Invalid size
            data=invalid_data
        )
        
        with pytest.raises(FileValidationError) as exc_info:
            self.validator.validate_file(image_file)
        
        # Should catch the first error it encounters
        assert "filename" in str(exc_info.value).lower() or \
               "content type" in str(exc_info.value).lower() or \
               "empty" in str(exc_info.value).lower()
    
    def test_validation_performance(self):
        """Test validation performance with large files."""
        import time
        
        # Create large valid file
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        large_data = jpeg_header + b'\x00' * (4 * 1024 * 1024)  # 4MB
        
        image_file = ImageFile(
            filename="large_file.jpg",
            content_type="image/jpeg",
            size=len(large_data),
            data=large_data
        )
        
        start_time = time.time()
        result = self.validator.validate_file(image_file)
        end_time = time.time()
        
        # Validation should complete quickly (< 1 second)
        assert end_time - start_time < 1.0
        assert result.is_valid is True
    
    @patch('app.services.file_validation.logger')
    def test_validation_logging(self, mock_logger):
        """Test that validation events are properly logged."""
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        image_file = ImageFile(
            filename="test_logging.jpg",
            content_type="image/jpeg",
            size=len(jpeg_data),
            data=jpeg_data
        )
        
        result = self.validator.validate_file(image_file)
        
        # Verify logging was called
        assert mock_logger.info.called or mock_logger.debug.called
        assert result.is_valid is True
    
    def test_concurrent_validation(self):
        """Test file validation with concurrent requests."""
        import threading
        import queue
        
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        results_queue = queue.Queue()
        
        def validate_file(file_number):
            try:
                image_file = ImageFile(
                    filename=f"concurrent_{file_number}.jpg",
                    content_type="image/jpeg",
                    size=len(jpeg_data),
                    data=jpeg_data
                )
                
                result = self.validator.validate_file(image_file)
                results_queue.put((file_number, result.is_valid))
            except Exception as e:
                results_queue.put((file_number, False))
        
        # Start multiple validation threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=validate_file, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all validations succeeded
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 5
        assert all(result[1] for result in results)  # All should be valid
