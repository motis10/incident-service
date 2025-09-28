"""
SharePoint client for NetanyaMuni API communication.
Handles multipart requests, WebKit boundaries, and municipality-specific headers.
"""
import json
import secrets
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.logging import get_logger
from app.models.sharepoint import APIPayload
from app.models.response import APIResponse
from app.services.file_validation import MultipartFile

logger = get_logger("sharepoint_client")


class SharePointError(Exception):
    """Raised when SharePoint API communication fails."""
    pass


@dataclass
class SharePointResponse:
    """SharePoint API response wrapper."""
    success: bool
    result_code: int
    error_description: str
    result_status: str
    data: str
    raw_response: Dict[str, Any]


@dataclass
class MultipartRequest:
    """Multipart request data for SharePoint submission."""
    boundary: str
    content_type: str
    body: bytes


class SharePointClient:
    """Client for SharePoint NetanyaMuni incidents.ashx API."""
    
    DEFAULT_ENDPOINT = "https://www.netanya.muni.il/_layouts/15/NetanyaMuni/incidents.ashx?method=CreateNewIncident"
    
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize SharePoint client.
        
        Args:
            endpoint_url: Custom SharePoint endpoint URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.endpoint_url = endpoint_url or self.DEFAULT_ENDPOINT
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Configure requests session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_required_headers(self) -> Dict[str, str]:
        """
        Get required headers for NetanyaMuni API.
        
        Returns:
            Dictionary of required headers
        """
        return {
            "Origin": "https://www.netanya.muni.il",
            "Referer": "https://www.netanya.muni.il/PublicComplaints.aspx",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "multipart/form-data",  # Will be updated with boundary
            "User-Agent": "Mozilla/5.0 (compatible; NetanyaIncidentService/1.0)"
        }
    
    def generate_webkit_boundary(self) -> str:
        """
        Generate WebKit-style boundary for multipart requests.
        
        Returns:
            WebKit boundary string
        """
        # Generate 16 random hex characters for WebKit boundary
        random_hex = secrets.token_hex(8)
        return f"----WebKitFormBoundary{random_hex}"
    
    def build_multipart_request(
        self,
        payload: APIPayload,
        file: Optional[MultipartFile] = None
    ) -> MultipartRequest:
        """
        Build multipart/form-data request for SharePoint.
        
        Args:
            payload: API payload data
            file: Optional file attachment
            
        Returns:
            MultipartRequest ready for submission
        """
        boundary = self.generate_webkit_boundary()
        content_type = f"multipart/form-data; boundary={boundary}"
        
        # Build multipart body
        body_parts = []
        
        # Add JSON field (required by SharePoint)
        json_data = payload.model_dump()
        body_parts.append(
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="json"\r\n'
            f'\r\n'
            f'{json.dumps(json_data, ensure_ascii=False)}\r\n'
        )
        
        # Add file attachment if provided
        if file:
            body_parts.append(
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="{file.field_name}"; '
                f'filename="{file.filename}"\r\n'
                f'Content-Type: {file.content_type}\r\n'
                f'\r\n'
            )
            # File data will be added as bytes
            body_text = ''.join(body_parts).encode('utf-8')
            body_text += file.data
            body_text += f'\r\n--{boundary}--\r\n'.encode('utf-8')
        else:
            # Close boundary without file
            body_parts.append(f'--{boundary}--\r\n')
            body_text = ''.join(body_parts).encode('utf-8')
        
        return MultipartRequest(
            boundary=boundary,
            content_type=content_type,
            body=body_text
        )
    
    def parse_sharepoint_response(self, response: requests.Response) -> APIResponse:
        """
        Parse SharePoint API response.
        
        Args:
            response: HTTP response from SharePoint
            
        Returns:
            Parsed APIResponse
            
        Raises:
            SharePointError: If response parsing fails or indicates error
        """
        try:
            # Check HTTP status
            if response.status_code != 200:
                raise SharePointError(
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
            
            # Parse JSON response
            try:
                response_data = response.json()
            except ValueError as e:
                raise SharePointError(f"Invalid JSON response: {str(e)}")
            
            # Extract SharePoint response fields
            result_code = response_data.get("ResultCode", 0)
            error_description = response_data.get("ErrorDescription", "")
            result_status = response_data.get("ResultStatus", "")
            data = response_data.get("data", "")
            
            # Check for SharePoint-level errors
            if result_code != 200 or "ERROR" in result_status.upper():
                raise SharePointError(
                    f"SharePoint API error (Code: {result_code}): {error_description}"
                )
            
            # Create successful response
            return APIResponse(
                ResultCode=result_code,
                ErrorDescription=error_description,
                ResultStatus=result_status,
                data=data
            )
            
        except SharePointError:
            raise
        except Exception as e:
            raise SharePointError(f"Failed to parse SharePoint response: {str(e)}")
    
    def submit_to_sharepoint(
        self,
        payload: APIPayload,
        file: Optional[MultipartFile] = None
    ) -> APIResponse:
        """
        Submit incident data to SharePoint NetanyaMuni API.
        
        Args:
            payload: Incident data payload
            file: Optional file attachment
            
        Returns:
            SharePoint API response
            
        Raises:
            SharePointError: If submission fails
        """
        try:
            # Build multipart request
            multipart_request = self.build_multipart_request(payload, file)
            
            # Prepare headers
            headers = self.get_required_headers()
            headers["Content-Type"] = multipart_request.content_type
            
            # Log request details (without sensitive data)
            logger.info(
                f"Submitting incident to SharePoint: "
                f"caller={payload.callerFirstName} {payload.callerLastName}, "
                f"category={payload.eventCallDesc}, "
                f"with_file={file is not None}"
            )
            
            # Make request with retries
            try:
                response = self.session.post(
                    self.endpoint_url,
                    data=multipart_request.body,
                    headers=headers,
                    timeout=self.timeout
                )
            except requests.exceptions.RequestException as e:
                raise SharePointError(f"Network error: {str(e)}")
            
            # Parse and return response
            api_response = self.parse_sharepoint_response(response)
            
            logger.info(
                f"SharePoint submission successful: "
                f"ticket_id={api_response.data}, "
                f"status={api_response.ResultStatus}"
            )
            
            return api_response
            
        except SharePointError:
            raise
        except Exception as e:
            raise SharePointError(f"Unexpected error during SharePoint submission: {str(e)}")
