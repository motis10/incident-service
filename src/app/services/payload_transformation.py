"""
Payload transformation service for converting request models to SharePoint format.
Handles municipality-specific value injection and field mapping.
"""
from typing import Optional

from app.core.logging import get_logger
from app.models.request import IncidentSubmissionRequest
from app.models.sharepoint import APIPayload

logger = get_logger("payload_transformation")


class TransformationError(Exception):
    """Raised when payload transformation fails."""
    pass


class NetanyaMuniConfig:
    """Configuration for NetanyaMuni fixed values."""
    
    def __init__(self):
        """Initialize NetanyaMuni configuration with fixed municipality values."""
        # Fixed municipality values as per NetanyaMuni requirements
        self.event_call_source_id = 4
        self.city_code = "7400"
        self.city_desc = "נתניה"
        self.event_call_center_id = "3"
        self.street_code = "898"
        self.street_desc = "קרל פופר"
        self.contact_us_type = "3"


class PayloadTransformer:
    """Service for transforming incident requests to SharePoint API format."""
    
    def __init__(self, config: Optional[NetanyaMuniConfig] = None):
        """
        Initialize payload transformer.
        
        Args:
            config: Optional NetanyaMuni configuration (uses default if not provided)
        """
        self.config = config or NetanyaMuniConfig()
    
    def transform_to_sharepoint(self, request: IncidentSubmissionRequest) -> APIPayload:
        """
        Transform incident submission request to SharePoint API payload.
        
        Args:
            request: Incident submission request from API
            
        Returns:
            APIPayload formatted for SharePoint submission
            
        Raises:
            TransformationError: If transformation fails
        """
        if request is None:
            raise TransformationError("request cannot be None")
        
        try:
            # Determine event call description (custom text takes priority)
            event_call_desc = self._get_event_call_description(request)
            
            # Extract user data with safe defaults for optional fields
            user_data = request.user_data
            caller_tz = getattr(user_data, 'user_id', None) or ""
            caller_email = getattr(user_data, 'email', None) or ""
            
            # Create SharePoint payload with fixed municipality values
            payload = APIPayload(
                # Fixed municipality values
                eventCallSourceId=self.config.event_call_source_id,
                cityCode=self.config.city_code,
                cityDesc=self.config.city_desc,
                eventCallCenterId=self.config.event_call_center_id,
                streetCode=self.config.street_code,
                streetDesc=self.config.street_desc,
                contactUsType=self.config.contact_us_type,
                
                # Dynamic values from request
                eventCallDesc=event_call_desc,
                houseNumber=request.street.house_number,
                callerFirstName=user_data.first_name,
                callerLastName=user_data.last_name,
                callerPhone1=user_data.phone,
                callerTZ=caller_tz,
                callerEmail=caller_email
            )
            
            # Log transformation (without sensitive data)
            logger.info(
                f"Transformed incident request: "
                f"caller={user_data.first_name} {user_data.last_name}, "
                f"category={request.category.name}, "
                f"house_number={request.street.house_number}"
            )
            
            return payload
            
        except Exception as e:
            logger.error(f"Failed to transform payload: {str(e)}")
            raise TransformationError(f"Transformation failed: {str(e)}")
    
    def _get_event_call_description(self, request: IncidentSubmissionRequest) -> str:
        """
        Get event call description with priority: custom text > category description.
        
        Args:
            request: Incident submission request
            
        Returns:
            Event call description text
        """
        # Check if custom text is provided and not empty/whitespace
        custom_text = getattr(request, 'custom_text', None)
        if custom_text and custom_text.strip():
            return custom_text
        
        # Fallback to category description
        return request.category.event_call_desc
