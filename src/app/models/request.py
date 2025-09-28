"""
Request models for the Netanya Incident Service API.
These models define the structure for incoming API requests.
"""
from typing import Optional
from pydantic import BaseModel, Field


class UserData(BaseModel):
    """User data for incident submission."""
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    phone: str = Field(..., description="User's phone number")
    user_id: Optional[str] = Field(None, description="User's ID number")
    email: Optional[str] = Field(None, description="User's email address")


class Category(BaseModel):
    """Incident category information."""
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    text: str = Field(..., description="Category description")
    image_url: str = Field(..., description="Category image URL")
    event_call_desc: str = Field(..., description="Event call description")


class StreetNumber(BaseModel):
    """Street and house number information."""
    id: int = Field(..., description="Street ID")
    name: str = Field(..., description="Street name")
    image_url: str = Field(..., description="Street image URL")
    house_number: str = Field(..., description="House number")


class ImageFile(BaseModel):
    """Image file for incident evidence."""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    data: str = Field(..., description="Base64 encoded file data")


class IncidentSubmissionRequest(BaseModel):
    """Complete incident submission request."""
    user_data: UserData = Field(..., description="User information")
    category: Category = Field(..., description="Incident category")
    street: StreetNumber = Field(..., description="Location information")
    custom_text: Optional[str] = Field(None, description="Custom description text")
    extra_files: Optional[ImageFile] = Field(None, description="Optional image attachment")
