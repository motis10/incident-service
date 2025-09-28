"""
Response models for the Netanya Incident Service API.
These models define the structure for API responses.
"""
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """Standard API response format compatible with SharePoint."""
    ResultCode: int = Field(..., description="Result code (200 for success, error codes for failures)")
    ErrorDescription: str = Field(..., description="Error description (empty for success)")
    ResultStatus: str = Field(..., description="Result status message")
    data: str = Field(..., description="Response data (ticket ID for success, empty for errors)")
