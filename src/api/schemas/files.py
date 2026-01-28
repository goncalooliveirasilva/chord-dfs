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
