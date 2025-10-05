"""
Error handling service for request validation and structured error responses.
Provides correlation ID generation and comprehensive error formatting.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pydantic import ValidationError

from app.core.logging import get_logger
from app.services.file_validation import ValidationResult

logger = get_logger("error_handling")


@dataclass
class ErrorDetails:
    """Detailed error information for specific fields. """
    field: str
    message: str
    type: str


@dataclass
class ValidationErrorResponse:
    """Structured validation error response."""
    error: str
    details: List[ErrorDetails]
    correlation_id: str


class CorrelationIdGenerator:
    """Generator for correlation IDs for request tracking."""
    
    def __init__(self):
        """Initialize the correlation ID generator."""
        pass
    
    def generate(self) -> str:
        """
        Generate a unique correlation ID.
        
        Returns:
            Unique correlation ID string
        """
        return str(uuid.uuid4())


class ErrorHandlingService:
    """Service for handling errors and creating structured error responses."""
    
    def __init__(self):
        """Initialize the error handling service."""
        self.correlation_generator = CorrelationIdGenerator()
    
    def handle_validation_error(
        self, 
        validation_error: ValidationError,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle Pydantic validation errors and convert to structured format.
        
        Args:
            validation_error: Pydantic ValidationError
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            Structured error response dictionary
        """
        if correlation_id is None:
            correlation_id = self.correlation_generator.generate()
        
        # Convert Pydantic errors to structured format
        error_details = []
        for error in validation_error.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            error_details.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
        
        response = {
            "error": "Validation failed",
            "details": error_details,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Log the error
        self.log_error(
            message="Validation error occurred",
            correlation_id=correlation_id,
            error_details={"validation_errors": error_details}
        )
        
        return response
    
    def handle_file_validation_error(
        self,
        validation_result: ValidationResult,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle file validation errors.
        
        Args:
            validation_result: File validation result with errors
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            Structured error response dictionary
        """
        if correlation_id is None:
            correlation_id = self.correlation_generator.generate()
        
        # Convert file validation errors to structured format
        error_details = []
        for error_message in validation_result.errors:
            error_details.append({
                "field": "extra_files",
                "message": error_message,
                "type": "file_validation_error"
            })
        
        response = {
            "error": "File validation failed",
            "details": error_details,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Log the error
        self.log_error(
            message="File validation error occurred",
            correlation_id=correlation_id,
            error_details={"file_errors": validation_result.errors}
        )
        
        return response
    
    def create_422_response(
        self,
        message: str,
        field_errors: List[Dict[str, str]],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create HTTP 422 Unprocessable Entity response.
        
        Args:
            message: Error message
            field_errors: List of field-specific errors
            correlation_id: Optional correlation ID
            
        Returns:
            Structured 422 error response
        """
        if correlation_id is None:
            correlation_id = self.correlation_generator.generate()
        
        return {
            "error": message,
            "status_code": 422,
            "details": field_errors,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def create_500_response(
        self,
        message: str,
        error_details: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create HTTP 500 Internal Server Error response.
        
        Args:
            message: Error message
            error_details: Optional detailed error information
            correlation_id: Optional correlation ID
            
        Returns:
            Structured 500 error response
        """
        if correlation_id is None:
            correlation_id = self.correlation_generator.generate()
        
        response = {
            "error": message,
            "status_code": 500,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if error_details:
            response["details"] = error_details
        
        # Log internal server errors
        self.log_error(
            message=f"Internal server error: {message}",
            correlation_id=correlation_id,
            error_details={"error_details": error_details}
        )
        
        return response
    
    def create_400_response(
        self,
        message: str,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create HTTP 400 Bad Request response.
        
        Args:
            message: Error message
            correlation_id: Optional correlation ID
            
        Returns:
            Structured 400 error response
        """
        if correlation_id is None:
            correlation_id = self.correlation_generator.generate()
        
        return {
            "error": message,
            "status_code": 400,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def create_field_validation_response(
        self,
        field_errors: List[ErrorDetails],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create field-level validation error response.
        
        Args:
            field_errors: List of ErrorDetails objects
            correlation_id: Optional correlation ID
            
        Returns:
            Structured validation error response
        """
        if correlation_id is None:
            correlation_id = self.correlation_generator.generate()
        
        # Convert ErrorDetails to dict format
        error_details = []
        for error in field_errors:
            error_details.append({
                "field": error.field,
                "message": error.message,
                "type": error.type
            })
        
        return {
            "error": "Field validation failed",
            "details": error_details,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def log_error(
        self,
        message: str,
        correlation_id: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log error with correlation ID for tracking.
        
        Args:
            message: Error message to log
            correlation_id: Correlation ID for request tracking
            error_details: Optional additional error details
        """
        log_data = {
            "correlation_id": correlation_id
        }
        
        if error_details:
            log_data.update(error_details)
        
        logger.error(f"Error occurred - {message} [correlation_id: {correlation_id}]", extra=log_data)
