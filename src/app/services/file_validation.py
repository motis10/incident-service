"""
File validation service for image upload capabilities.
Provides validation for image files before SharePoint submission.
"""
import base64
from typing import List
from dataclasses import dataclass
from app.models.request import ImageFile


class FileValidationError(Exception):
    """Raised when file validation fails."""
    pass


@dataclass
class ValidationResult:
    """Result of file validation."""
    is_valid: bool
    errors: List[str]


@dataclass
class MultipartFile:
    """Prepared file for multipart upload."""
    field_name: str
    filename: str
    content_type: str
    data: bytes


class FileValidationService:
    """Service for validating image files and preparing them for upload."""
    
    # Supported image MIME types
    SUPPORTED_FORMATS = {
        "image/jpeg",
        "image/png", 
        "image/gif",
        "image/webp"
    }
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    def __init__(self):
        """Initialize the file validation service."""
        pass
    
    def validate_file(self, image_file: ImageFile) -> ValidationResult:
        """
        Validate an image file for upload.
        
        Args:
            image_file: The image file to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        
        # Validate file format
        if not self._validate_file_format(image_file.content_type):
            errors.append(f"Unsupported file format: {image_file.content_type}. "
                         f"Supported formats: {', '.join(sorted(self.SUPPORTED_FORMATS))}")
        
        # Validate file size
        if not self._validate_file_size(image_file.size):
            if image_file.size == 0:
                errors.append("File is empty")
            else:
                max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                errors.append(f"File size ({image_file.size} bytes) exceeds maximum allowed "
                             f"size of {max_size_mb}MB")
        
        # Validate base64 data
        if not self._validate_base64_data(image_file.data):
            errors.append("Invalid base64 encoded data")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors)
    
    def validate_file_type(self, content_type: str, data: bytes) -> bool:
        """
        Validate file type and MIME type.
        
        Args:
            content_type: MIME type of the file
            data: File data bytes
            
        Returns:
            True if file type is valid, False otherwise
        """
        return self._validate_file_format(content_type)
    
    def validate_file_size(self, size: int) -> bool:
        """
        Validate file size.
        
        Args:
            size: File size in bytes
            
        Returns:
            True if file size is valid, False otherwise
        """
        return self._validate_file_size(size)
    
    def prepare_multipart_file(self, image_file: ImageFile) -> MultipartFile:
        """
        Prepare an image file for multipart upload to SharePoint.
        
        Args:
            image_file: Validated image file
            
        Returns:
            MultipartFile ready for upload
            
        Raises:
            FileValidationError: If file preparation fails
        """
        try:
            # Decode base64 data to bytes
            file_data = base64.b64decode(image_file.data)
            
            return MultipartFile(
                field_name="attachment",
                filename=image_file.filename,
                content_type=image_file.content_type,
                data=file_data
            )
        except Exception as e:
            raise FileValidationError(f"Failed to prepare multipart file: {str(e)}")
    
    def _validate_file_format(self, content_type: str) -> bool:
        """Validate that the file format is supported."""
        return content_type in self.SUPPORTED_FORMATS
    
    def _validate_file_size(self, size: int) -> bool:
        """Validate that the file size is within limits."""
        return 0 < size <= self.MAX_FILE_SIZE
    
    def _validate_base64_data(self, data: str) -> bool:
        """Validate that the data is valid base64."""
        if not data:
            return False
        
        try:
            # Validate base64 format
            base64.b64decode(data, validate=True)
            # Additional check: ensure the string doesn't contain invalid characters
            import re
            base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
            return bool(base64_pattern.match(data))
        except Exception:
            return False
