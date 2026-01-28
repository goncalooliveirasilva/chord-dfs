"""File routes for the Chord DFS API."""

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from src.api.schemas.files import (
    FileDeleteResponse,
    FileListResponse,
    FileUploadResponse,
)

router = APIRouter(prefix="/files", tags=["files"])

# Type alias for file upload dependency
UploadFileDep = Annotated[UploadFile, File()]


@router.post("", response_model=FileUploadResponse, status_code=201)
async def upload_file(file: UploadFileDep) -> FileUploadResponse:
    """Upload a file to the distributed file system.

    The file will be stored on the node responsible for its key
    (determined by hashing the filename).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # TODO: Implement with node service

    return FileUploadResponse(
        message=f"File {file.filename} uploaded successfully",
        filename=file.filename,
    )


@router.get("", response_model=FileListResponse)
async def list_files() -> FileListResponse:
    """List all files stored on the ring."""
    # TODO: Implement with node service
    files: list[str] = []
    return FileListResponse(files=files)


@router.get("/{filename}")
async def get_file(filename: str) -> Response:
    """Download a file from the distributed file system.

    The request will be routed to the node responsible for the file.
    """
    # TODO: Implement with node service

    raise HTTPException(status_code=404, detail="File not found")


@router.delete("/{filename}", response_model=FileDeleteResponse)
async def delete_file(filename: str) -> FileDeleteResponse:
    """Delete a file from the distributed file system."""
    # TODO: Implement with node service
    raise HTTPException(status_code=404, detail="File not found")


@router.post("/forward", response_model=FileUploadResponse, status_code=201)
async def forward_file(file: UploadFileDep) -> FileUploadResponse:
    """Internal endpoint for forwarding files between nodes."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # TODO: Implement with node service

    return FileUploadResponse(
        message="File stored successfully",
        filename=file.filename or "",
    )


@router.get("/list/local", response_model=FileListResponse)
async def list_local_files() -> FileListResponse:
    """List files stored locally on this node."""
    # TODO: Implement with node service
    files: list[str] = []
    return FileListResponse(files=files)
