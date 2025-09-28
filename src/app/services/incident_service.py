"""
Integrated incident service for complete incident submission workflow.
Combines payload transformation, file validation, and SharePoint submission.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.core.logging import get_logger
from app.models.request import IncidentSubmissionRequest
from app.services.payload_transformation import PayloadTransformer
from app.services.file_validation import FileValidationService
from app.clients.sharepoint import SharePointClient, SharePointError
from app.services.error_handling import ErrorHandlingService

logger = get_logger("incident_service")


class IncidentSubmissionError(Exception):
    """Raised when incident submission fails."""
    pass


@dataclass
class SubmissionResult:
    """Result of incident submission."""
    success: bool
    ticket_id: str
    correlation_id: str
    has_file: bool
    file_info: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


class IncidentService:
    """
    Integrated service for complete incident submission workflow.
    Handles validation, transformation, and SharePoint submission.
    """
    
    def __init__(
        self,
        payload_transformer: Optional[PayloadTransformer] = None,
        file_service: Optional[FileValidationService] = None,
        sharepoint_client: Optional[SharePointClient] = None,
        error_service: Optional[ErrorHandlingService] = None
    ):
        """
        Initialize incident service with all dependencies.
        
        Args:
            payload_transformer: Payload transformation service
            file_service: File validation service
            sharepoint_client: SharePoint API client
            error_service: Error handling service
        """
        self.payload_transformer = payload_transformer or PayloadTransformer()
        self.file_service = file_service or FileValidationService()
        self.sharepoint_client = sharepoint_client or SharePointClient()
        self.error_service = error_service or ErrorHandlingService()
    
    def submit_incident(self, request: IncidentSubmissionRequest) -> SubmissionResult:
        """
        Submit incident to SharePoint with complete validation and transformation.
        
        Args:
            request: Incident submission request
            
        Returns:
            SubmissionResult with ticket ID and metadata
            
        Raises:
            IncidentSubmissionError: If submission fails
        """
        correlation_id = self.error_service.correlation_generator.generate()
        
        try:
            # Log incident submission start
            logger.info(
                f"Starting incident submission [correlation_id: {correlation_id}]: "
                f"caller={request.user_data.first_name} {request.user_data.last_name}, "
                f"category={request.category.name}, "
                f"has_file={request.extra_files is not None}"
            )
            
            # 1. Validate file if present
            multipart_file = None
            file_info = None
            
            if request.extra_files:
                file_validation = self.file_service.validate_file(request.extra_files)
                if not file_validation.is_valid:
                    raise IncidentSubmissionError(
                        f"File validation failed: {', '.join(file_validation.errors)}"
                    )
                
                # Prepare multipart file for SharePoint
                multipart_file = self.file_service.prepare_multipart_file(request.extra_files)
                file_info = {
                    "filename": request.extra_files.filename,
                    "content_type": request.extra_files.content_type,
                    "size": request.extra_files.size
                }
                
                logger.info(
                    f"File validated successfully [correlation_id: {correlation_id}]: "
                    f"filename={request.extra_files.filename}, "
                    f"size={request.extra_files.size} bytes"
                )
            
            # 2. Transform request to SharePoint payload
            payload = self.payload_transformer.transform_to_sharepoint(request)
            
            logger.info(
                f"Payload transformed [correlation_id: {correlation_id}]: "
                f"eventCallDesc={payload.eventCallDesc[:50]}..."
            )
            
            # 3. Submit to SharePoint
            try:
                api_response = self.sharepoint_client.submit_to_sharepoint(
                    payload, 
                    file=multipart_file
                )
                
                logger.info(
                    f"SharePoint submission successful [correlation_id: {correlation_id}]: "
                    f"ticket_id={api_response.data}, "
                    f"status={api_response.ResultStatus}"
                )
                
                # Create success result
                return SubmissionResult(
                    success=True,
                    ticket_id=api_response.data,
                    correlation_id=correlation_id,
                    has_file=request.extra_files is not None,
                    file_info=file_info,
                    metadata={
                        "correlation_id": correlation_id,
                        "sharepoint_status": api_response.ResultStatus,
                        "submission_timestamp": payload.__dict__.get("timestamp"),
                        "file_processed": multipart_file is not None
                    }
                )
                
            except SharePointError as e:
                logger.error(
                    f"SharePoint submission failed [correlation_id: {correlation_id}]: {str(e)}"
                )
                raise IncidentSubmissionError(f"SharePoint submission failed: {str(e)}")
            
        except IncidentSubmissionError:
            # Re-raise incident submission errors
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during incident submission [correlation_id: {correlation_id}]: {str(e)}"
            )
            raise IncidentSubmissionError(f"Incident submission failed: {str(e)}")
