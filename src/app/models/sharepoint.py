"""
SharePoint integration models for the Netanya Incident Service.
These models define the structure for SharePoint API communication.
"""
from pydantic import BaseModel, Field


class APIPayload(BaseModel):
    """Payload format for SharePoint NetanyaMuni incidents.ashx endpoint."""
    
    # Fixed municipality values
    eventCallSourceId: int = Field(..., description="Event call source ID (fixed: 4)")
    cityCode: str = Field(..., description="City code (fixed: 7400)")
    cityDesc: str = Field(..., description="City description (fixed: נתניה)")
    eventCallCenterId: str = Field(..., description="Event call center ID (fixed: 3)")
    streetCode: str = Field(..., description="Street code (fixed: 898)")
    streetDesc: str = Field(..., description="Street description (fixed: קרל פופר)")
    contactUsType: str = Field(..., description="Contact us type (fixed: 3)")
    
    # Dynamic values from request
    eventCallDesc: str = Field(..., description="Event call description from custom text or category")
    houseNumber: str = Field(..., description="House number from street information")
    callerFirstName: str = Field(..., description="Caller's first name")
    callerLastName: str = Field(..., description="Caller's last name")
    callerTZ: str = Field(..., description="Caller's ID number")
    callerPhone1: str = Field(..., description="Caller's phone number")
    callerEmail: str = Field(..., description="Caller's email address")
