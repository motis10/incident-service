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
            "Referer": "https://www.netanya.muni.il/CityHall/ServicesInnovation/Pages/PublicComplaints.aspx",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "multipart/form-data",  # Will be updated with boundary
            "User-Agent": "Mozilla/5.0 (compatible; NetanyaIncidentService/1.0)",
            "Accept": "application/json;odata=verbose",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br"
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
                logger.error(f"HTTP error response: {response.status_code}")
                logger.error(f"Error response headers: {dict(response.headers)}")
                logger.error(f"Error response body: {response.text}")
                logger.error(f"Error response content length: {len(response.content)} bytes")
                raise SharePointError(
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
            
            # Log comprehensive response details
            logger.info(f"SharePoint response status: {response.status_code}")
            logger.info(f"SharePoint response headers: {dict(response.headers)}")
            logger.info(f"Raw SharePoint response body: {response.text}")
            logger.info(f"Response content length: {len(response.content)} bytes")
            logger.info(f"Response encoding: {response.encoding}")
            
            # Parse JSON response
            try:
                response_data = response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response text that failed to parse: {response.text}")
                raise SharePointError(f"Invalid JSON response: {str(e)}")
            
            # Log full JSON response
            logger.info(f"Parsed JSON response: {response_data}")
            
            # Log all SharePoint response parameters
            logger.info(
                f"SharePoint response received: "
                f"status_code={response.status_code}, "
                f"ResultCode={response_data.get('ResultCode', 'N/A')}, "
                f"ResultStatus={response_data.get('ResultStatus', 'N/A')}, "
                f"ErrorDescription={response_data.get('ErrorDescription', 'N/A')}, "
                f"data={response_data.get('data', 'N/A')}, "
                f"response_size={len(response.text)} chars"
            )
            
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
    
    def establish_session(self) -> None:
        """
        Establish a session with SharePoint by visiting the main page first.
        This helps with Cloudflare cookie requirements and gets proper session cookies.
        """
        try:
            logger.info("Establishing session with SharePoint...")
            
            # First, visit the main services page to get cookies
            session_response = self.session.get(
                "https://www.netanya.muni.il/CityHall/ServicesInnovation/Pages/default.aspx",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "he-IL,he;q=0.9,en-US,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Dnt": "1",
                    "Sec-Ch-Ua": '"Chromium";v="141", "Not?A_Brand";v="8"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"macOS"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1"
                },
                timeout=self.timeout,
                allow_redirects=True
            )
            
            logger.info(f"Session establishment response: {session_response.status_code}")
            logger.info(f"Session cookies received: {dict(self.session.cookies)}")
            
            # Check for specific important cookies
            important_cookies = ['_cflb', 'TRINITY_USER_DATA', 'TRINITY_USER_ID', 'SearchSession', 'WSS_FullScreenMode']
            received_cookies = [cookie for cookie in important_cookies if cookie in self.session.cookies]
            logger.info(f"Important cookies received: {received_cookies}")
            
            if session_response.status_code == 200:
                logger.info("Session established successfully")
            else:
                logger.warning(f"Session establishment returned status {session_response.status_code}")
                
        except Exception as e:
            logger.warning(f"Failed to establish session: {str(e)}")
            # Continue anyway - some APIs work without pre-session

    def verify_session_cookies(self) -> None:
        """
        Verify that we have the essential cookies for SharePoint API calls.
        """
        essential_cookies = ['_cflb', 'TRINITY_USER_DATA', 'TRINITY_USER_ID']
        missing_cookies = [cookie for cookie in essential_cookies if cookie not in self.session.cookies]
        
        if missing_cookies:
            logger.warning(f"Missing essential cookies: {missing_cookies}")
            logger.warning("API call may fail due to missing session cookies")
        else:
            logger.info("All essential cookies present for API call")
        
        # Log all cookies for debugging
        logger.info(f"Current session cookies: {list(self.session.cookies.keys())}")

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
            # Establish session first to handle Cloudflare cookies
            self.establish_session()
            
            # Small delay to allow Cloudflare to process the session
            time.sleep(10)
            
            # Verify we have essential cookies
            self.verify_session_cookies()
            
            # Build multipart request
            multipart_request = self.build_multipart_request(payload, file)
            
            # Prepare headers
            headers = self.get_required_headers()
            headers["Content-Type"] = multipart_request.content_type
            
            # Log request details (without sensitive data)
            logger.info(
                f"Submitting incident to SharePoint: "
                f"caller={payload.callerFirstName} {payload.callerLastName}, "
                f"phone={payload.callerPhone1}, "
                f"category={payload.eventCallDesc}, "
                f"street={payload.streetDesc} {payload.houseNumber}, "
                f"with_file={file is not None}, "
                f"endpoint={self.endpoint_url}, "
                f"timeout={self.timeout}s"
            )
            
            # Log multipart request body details
            logger.info(
                f"Multipart request body: "
                f"content_type={multipart_request.content_type}, "
                f"body_size={len(multipart_request.body)} bytes, "
                f"body_preview={multipart_request.body[:1000].decode('utf-8', errors='ignore')}..."
            )
            
            # Log full request details for debugging
            logger.info(f"Full request headers: {headers}")
            logger.info(f"Full request body: {multipart_request.body.decode('utf-8', errors='ignore')}")
            
            # Make request with retries
            try:
                response = self.session.post(
                    self.endpoint_url,
                    data=multipart_request.body,
                    headers=headers,
                    timeout=self.timeout
                )
            except requests.exceptions.RequestException as e:
                logger.error(f"Network request failed: {type(e).__name__}: {str(e)}")
                logger.error(f"Request details: url={self.endpoint_url}, timeout={self.timeout}")
                logger.error(f"Request headers: {headers}")
                logger.error(f"Request body size: {len(multipart_request.body)} bytes")
                logger.error(f"Request body preview: {multipart_request.body[:500].decode('utf-8', errors='ignore')}")
                logger.error(f"Exception details: {e.__dict__}")
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
            logger.error(f"Unexpected error during SharePoint submission: {type(e).__name__}: {str(e)}")
            logger.error(f"Error details: {e.__dict__}")
            logger.error(f"Request context: endpoint={self.endpoint_url}, payload={payload}")
            raise SharePointError(f"Unexpected error during SharePoint submission: {str(e)}")
