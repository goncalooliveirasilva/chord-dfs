"""File routes for the Chord DFS API."""

import mimetypes
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse

from src.api.schemas.files import (
    FileDeleteResponse,
    FileListResponse,
    FileUploadResponse,
)
from src.services.node_service import NodeService

router = APIRouter(prefix="/files", tags=["files"])

# Type alias for file upload dependency
UploadFileDep = Annotated[UploadFile, File()]


def get_node_service(request: Request) -> NodeService:
    """Dependency to get NodeService from app state."""
    return request.app.state.node_service


NodeServiceDep = Annotated[NodeService, Depends(get_node_service)]


@router.post("", response_model=FileUploadResponse, status_code=201)
async def upload_file(file: UploadFileDep, node_service: NodeServiceDep) -> FileUploadResponse:
    """Upload a file to the distributed file system.

    The file will be stored on the node responsible for its key
    (determined by hashing the filename).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    success, node_id = await node_service.put_file(file.filename, content)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to store file: {node_id}")

    return FileUploadResponse(
        message=f"File {file.filename} uploaded successfully to node {node_id}",
        filename=file.filename,
    )


@router.get("", response_model=FileListResponse)
async def list_files(node_service: NodeServiceDep) -> FileListResponse:
    """List all files stored locally on this node."""
    files = await node_service.list_local_files()
    return FileListResponse(files=files)


@router.get("/{filename}")
async def get_file(filename: str, node_service: NodeServiceDep) -> Response:
    """Download a file from the distributed file system.

    The request will be routed to the node responsible for the file.
    Returns a streaming response for efficient large file downloads.
    """
    content = await node_service.get_file(filename)

    if content is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Determine the content type
    content_type, _ = mimetypes.guess_type(filename)
    if content_type is None:
        content_type = "application/octet-stream"

    # Stream the content
    async def content_generator():
        yield content

    return StreamingResponse(
        content_generator(),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )


@router.delete("/{filename}", response_model=FileDeleteResponse)
async def delete_file(filename: str, node_service: NodeServiceDep) -> FileDeleteResponse:
    """Delete a file from the distributed file system."""
    success = await node_service.delete_file(filename)

    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return FileDeleteResponse(
        message=f"File {filename} deleted successfully",
        filename=filename,
    )


@router.post("/forward", response_model=FileUploadResponse, status_code=201)
async def forward_file(file: UploadFileDep, node_service: NodeServiceDep) -> FileUploadResponse:
    """Internal endpoint for forwarding files between nodes.

    This endpoint is called by other nodes to store files that this node
    is responsible for.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    await node_service.store_file_locally(file.filename, content)

    return FileUploadResponse(
        message="File stored successfully",
        filename=file.filename,
    )


@router.get("/list/local", response_model=FileListResponse)
async def list_local_files(node_service: NodeServiceDep) -> FileListResponse:
    """List files stored locally on this node."""
    files = await node_service.list_local_files()
    return FileListResponse(files=files)
