"""
Incident submission API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.logging import get_logger
from app.core.config import ConfigService
from app.models.request import IncidentSubmissionRequest
from app.services.incident_service import IncidentService, IncidentSubmissionError
from app.services.error_handling import ErrorHandlingService
from app.services.mock_service import MockSharePointService
from app.clients.sharepoint import SharePointClient

logger = get_logger("api.incidents")

# Initialize services
config_service = ConfigService()
config = config_service.get_config()
error_service = ErrorHandlingService()

# Create SharePoint client based on debug mode
def create_sharepoint_client():
    """Create SharePoint client based on configuration."""
    if config.debug_mode:
        logger.info("Debug mode enabled - using mock SharePoint service")
        return MockSharePointService()
    else:
        logger.info("Production mode - using production SharePoint client")
        from app.services.production_service import ProductionSharePointClient
        return ProductionSharePointClient()

# Initialize incident service
sharepoint_client = create_sharepoint_client()
incident_service = IncidentService(sharepoint_client=sharepoint_client)

# Create API router
router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.options("/submit")
async def submit_incident_options():
    """Handle CORS preflight request for incident submission."""
    return {"message": "CORS preflight successful"}

@router.post("/submit")
async def submit_incident(request: Request, incident_request: IncidentSubmissionRequest):
    """
    Submit incident to NetanyaMuni SharePoint system.
    
    Args:
        request: FastAPI request object
        incident_request: Incident submission data
        
    Returns:
        JSON response with submission result
        
    Raises:
        HTTPException: For various error conditions (400, 413, 422, 500)
    """
    correlation_id = error_service.correlation_generator.generate()
    
    try:
        # Log API request
        logger.info(
            f"Incident submission API request [correlation_id: {correlation_id}]: "
            f"caller={incident_request.user_data.first_name} {incident_request.user_data.last_name}, "
            f"category={incident_request.category.name}, "
            f"has_file={incident_request.extra_files is not None}"
        )
        
        # Check file size if present (413 - Request Entity Too Large)
        if incident_request.extra_files and incident_request.extra_files.size > 10 * 1024 * 1024:
            logger.warning(f"File too large [correlation_id: {correlation_id}]: {incident_request.extra_files.size} bytes")
            error_response = error_service.create_400_response(
                message="File size exceeds maximum limit of 10MB",
                correlation_id=correlation_id
            )
            error_response["status_code"] = 413
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content=error_response
            )
        
        # Submit incident
        try:
            result = incident_service.submit_incident(incident_request)
            
            # Create success response
            response_data = {
                "success": result.success,
                "ticket_id": result.ticket_id,
                "correlation_id": result.correlation_id,
                "has_file": result.has_file,
                "message": "Incident submitted successfully"
            }
            
            # Add file info if present
            if result.file_info:
                response_data["file_info"] = result.file_info
            
            # Add metadata in debug mode
            if config.debug_mode and result.metadata:
                response_data["metadata"] = result.metadata
            
            logger.info(
                f"Incident submission successful [correlation_id: {correlation_id}]: "
                f"ticket_id={result.ticket_id}"
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data,
                headers={
                    "X-Correlation-ID": result.correlation_id,
                    "X-API-Version": "1.0"
                }
            )
            
        except IncidentSubmissionError as e:
            # Handle incident submission errors (422 - Unprocessable Entity)
            logger.error(f"Incident submission failed [correlation_id: {correlation_id}]: {str(e)}")
            
            if "file validation" in str(e).lower():
                error_response = error_service.create_422_response(
                    message=str(e),
                    field_errors=[],
                    correlation_id=correlation_id
                )
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content=error_response
                )
            else:
                # Other incident submission errors
                error_response = error_service.create_500_response(
                    message="Incident submission failed",
                    error_details=str(e),
                    correlation_id=correlation_id
                )
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=error_response
                )
        
    except ValidationError as e:
        # Handle Pydantic validation errors (422 - Unprocessable Entity)
        logger.warning(f"Validation error [correlation_id: {correlation_id}]: {str(e)}")
        validation_response = error_service.handle_validation_error(e, correlation_id)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=validation_response
        )
        
    except Exception as e:
        # Handle unexpected errors (500 - Internal Server Error)
        logger.error(f"Unexpected API error [correlation_id: {correlation_id}]: {str(e)}")
        error_response = error_service.create_500_response(
            message="Internal server error",
            error_details=str(e),
            correlation_id=correlation_id
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )
