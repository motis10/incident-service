"""
Mock service for debug mode with consistent response generation.
Provides realistic SharePoint API simulation without external calls.
"""
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.core.logging import get_logger
from app.models.sharepoint import APIPayload
from app.services.file_validation import MultipartFile

logger = get_logger("mock_service")


@dataclass
class MockResponse:
    """Mock SharePoint API response."""
    result_code: int
    error_description: str
    result_status: str
    data: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to SharePoint API response format."""
        return {
            "ResultCode": self.result_code,
            "ErrorDescription": self.error_description,
            "ResultStatus": self.result_status,
            "data": self.data
        }


class MockTicketGenerator:
    """Generator for consistent mock ticket IDs with timestamp."""
    
    def __init__(self):
        """Initialize ticket generator."""
        self._counter = 0
    
    def generate_ticket_id(self) -> str:
        """
        Generate mock ticket ID in format: NETANYA-YYYY-NNNNNN
        
        Returns:
            Mock ticket ID string
        """
        # Get current year
        current_year = datetime.now().year
        
        # Generate unique number based on timestamp and counter
        timestamp_ms = int(time.time() * 1000)
        self._counter += 1
        
        # Use last 6 digits of timestamp + counter for uniqueness
        unique_number = (timestamp_ms + self._counter) % 1000000
        ticket_number = f"{unique_number:06d}"
        
        return f"NETANYA-{current_year}-{ticket_number}"


class MockSharePointService:
    """
    Mock SharePoint service for debug mode.
    Simulates SharePoint API responses without external calls.
    """
    
    def __init__(self):
        """Initialize mock SharePoint service."""
        self.ticket_generator = MockTicketGenerator()
        self._simulate_error = False
        self._error_message = ""
        self._error_code = 500
    
    def simulate_success(self) -> None:
        """Configure service to simulate successful responses."""
        self._simulate_error = False
        logger.info("Mock service configured for success simulation")
    
    def simulate_error(self, error_message: str, error_code: int = 500) -> None:
        """
        Configure service to simulate error responses.
        
        Args:
            error_message: Error message to return
            error_code: HTTP-like error code to return
        """
        self._simulate_error = True
        self._error_message = error_message
        self._error_code = error_code
        logger.info(f"Mock service configured for error simulation: {error_code} - {error_message}")
    
    def submit_incident(
        self, 
        payload: APIPayload, 
        file: Optional[MultipartFile] = None
    ) -> MockResponse:
        """
        Submit incident to mock SharePoint service.
        
        Args:
            payload: Incident payload data
            file: Optional file attachment
            
        Returns:
            MockResponse simulating SharePoint API
        """
        # Log mock submission for debugging
        logger.info(
            f"Mock SharePoint submission: "
            f"caller={payload.callerFirstName} {payload.callerLastName}, "
            f"eventCallDesc={payload.eventCallDesc[:50]}..., "
            f"has_file={file is not None}"
        )
        
        # Simulate error if configured
        if self._simulate_error:
            logger.info(f"Simulating error response: {self._error_code} - {self._error_message}")
            return MockResponse(
                result_code=self._error_code,
                error_description=self._error_message,
                result_status="ERROR",
                data=""
            )
        
        # Generate mock successful response
        ticket_id = self.ticket_generator.generate_ticket_id()
        
        logger.info(f"Mock successful submission: ticket_id={ticket_id}")
        
        return MockResponse(
            result_code=200,
            error_description="",
            result_status="SUCCESS CREATE",
            data=ticket_id
        )
    
    def submit_to_sharepoint(
        self, 
        payload: APIPayload, 
        file: Optional[MultipartFile] = None
    ) -> 'MockAPIResponse':
        """
        Submit to SharePoint (compatibility method).
        
        Args:
            payload: Incident payload data
            file: Optional file attachment
            
        Returns:
            MockAPIResponse compatible with SharePoint client interface
        """
        mock_response = self.submit_incident(payload, file)
        
        # Convert to APIResponse-compatible format
        return MockAPIResponse(
            ResultCode=mock_response.result_code,
            ErrorDescription=mock_response.error_description,
            ResultStatus=mock_response.result_status,
            data=mock_response.data
        )


class MockAPIResponse:
    """Mock API response compatible with SharePoint client interface."""
    
    def __init__(self, ResultCode: int, ErrorDescription: str, ResultStatus: str, data: str):
        """Initialize mock API response."""
        self.ResultCode = ResultCode
        self.ErrorDescription = ErrorDescription
        self.ResultStatus = ResultStatus
        self.data = data
