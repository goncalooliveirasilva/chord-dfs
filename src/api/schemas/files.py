"""Pydantic schemas for file operations."""

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """Response for successful file upload."""

    message: str
    filename: str


class FileDeleteResponse(BaseModel):
    """Response for successful file deletion."""

    message: str
    filename: str


class FileListResponse(BaseModel):
    """Response for listing files."""

    files: list[str]


class ErrorResponse(BaseModel):
    """Response for error cases."""

    error: str


class TransferRequest(BaseModel):
    """Request to get files in a key range for migration."""

    start_key: int  # Exclusive
    end_key: int  # Inclusive


class FileData(BaseModel):
    """File data for transfer."""

    filename: str
    content: str  # Base64 encoded


class TransferResponse(BaseModel):
    """Response containing files in the requested range."""

    files: list[FileData]
