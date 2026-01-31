"""API tests for file endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import create_app
from src.config import Settings


@pytest.fixture
def mock_node_service():
    """Create a mock NodeService."""
    service = AsyncMock()
    service.node_id = 100
    service.address = AsyncMock()
    service.address.host = "localhost"
    service.address.port = 5000
    service.start = AsyncMock()
    service.stop = AsyncMock()
    service.put_file = AsyncMock(return_value=(True, "100"))
    service.get_file = AsyncMock(return_value=b"file content")
    service.delete_file = AsyncMock(return_value=True)
    service.list_local_files = AsyncMock(return_value=["file1.txt", "file2.txt"])
    service.store_file_locally = AsyncMock(return_value="/path/to/file.txt")
    return service


@pytest.fixture
def test_settings(tmp_path):
    """Create test settings."""
    return Settings(
        host="localhost",
        port=5000,
        storage_path=str(tmp_path),
    )


@pytest.fixture
async def client(test_settings, mock_node_service):
    """Create a test client with mocked NodeService."""
    with patch("src.api.app.NodeService", return_value=mock_node_service):
        app = create_app(settings=test_settings)
        app.state.node_service = mock_node_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client


class TestUploadFile:
    """Tests for POST /files endpoint."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, client, mock_node_service):
        """Upload a file successfully."""
        mock_node_service.put_file.return_value = (True, "100")

        response = await client.post(
            "/files",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert "uploaded successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_upload_file_no_filename(self, client):
        """Upload with no filename returns error."""
        response = await client.post(
            "/files",
            files={"file": ("", b"hello world", "text/plain")},
        )

        # FastAPI returns 422 for validation errors, our code returns 400
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_upload_file_failure(self, client, mock_node_service):
        """Upload failure returns 500."""
        mock_node_service.put_file.return_value = (False, "Storage error")

        response = await client.post(
            "/files",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )

        assert response.status_code == 500
        assert "Failed to store" in response.json()["detail"]


class TestGetFile:
    """Tests for GET /files/{filename} endpoint."""

    @pytest.mark.asyncio
    async def test_get_file_success(self, client, mock_node_service):
        """Get a file successfully."""
        mock_node_service.get_file.return_value = b"file content"

        response = await client.get("/files/test.txt")

        assert response.status_code == 200
        assert response.content == b"file content"
        assert "attachment" in response.headers["content-disposition"]

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, client, mock_node_service):
        """Get nonexistent file returns 404."""
        mock_node_service.get_file.return_value = None

        response = await client.get("/files/nonexistent.txt")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_file_content_type(self, client, mock_node_service):
        """Get file returns correct content type."""
        mock_node_service.get_file.return_value = b"<html></html>"

        response = await client.get("/files/page.html")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestDeleteFile:
    """Tests for DELETE /files/{filename} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_file_success(self, client, mock_node_service):
        """Delete a file successfully."""
        mock_node_service.delete_file.return_value = True

        response = await client.delete("/files/test.txt")

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"
        assert "deleted" in data["message"]

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, client, mock_node_service):
        """Delete nonexistent file returns 404."""
        mock_node_service.delete_file.return_value = False

        response = await client.delete("/files/nonexistent.txt")

        assert response.status_code == 404


class TestListFiles:
    """Tests for GET /files endpoint."""

    @pytest.mark.asyncio
    async def test_list_files_success(self, client, mock_node_service):
        """List files successfully."""
        mock_node_service.list_local_files.return_value = ["file1.txt", "file2.txt"]

        response = await client.get("/files")

        assert response.status_code == 200
        data = response.json()
        assert data["files"] == ["file1.txt", "file2.txt"]

    @pytest.mark.asyncio
    async def test_list_files_empty(self, client, mock_node_service):
        """List files returns empty list."""
        mock_node_service.list_local_files.return_value = []

        response = await client.get("/files")

        assert response.status_code == 200
        assert response.json()["files"] == []


class TestListLocalFiles:
    """Tests for GET /files/list/local endpoint."""

    @pytest.mark.asyncio
    async def test_list_local_files(self, client, mock_node_service):
        """List local files successfully."""
        mock_node_service.list_local_files.return_value = ["local1.txt"]

        response = await client.get("/files/list/local")

        assert response.status_code == 200
        assert response.json()["files"] == ["local1.txt"]


class TestForwardFile:
    """Tests for POST /files/forward endpoint."""

    @pytest.mark.asyncio
    async def test_forward_file_success(self, client, mock_node_service):
        """Forward a file successfully."""
        mock_node_service.store_file_locally.return_value = "/path/to/file.txt"

        response = await client.post(
            "/files/forward",
            files={"file": ("test.txt", b"forwarded content", "text/plain")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert "stored successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_forward_file_no_filename(self, client):
        """Forward with no filename returns error."""
        response = await client.post(
            "/files/forward",
            files={"file": ("", b"content", "text/plain")},
        )

        # FastAPI returns 422 for validation errors, our code returns 400
        assert response.status_code in (400, 422)


class TestTransferFiles:
    """Tests for POST /files/transfer endpoint."""

    @pytest.mark.asyncio
    async def test_transfer_files_success(self, client, mock_node_service):
        """Transfer files in range returns base64 encoded files."""
        import base64

        mock_node_service.get_files_in_range.return_value = [
            ("file1.txt", b"content1"),
            ("file2.txt", b"content2"),
        ]

        response = await client.post(
            "/files/transfer",
            json={"start_key": 0, "end_key": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 2

        # Verify base64 encoding
        assert data["files"][0]["filename"] == "file1.txt"
        assert base64.b64decode(data["files"][0]["content"]) == b"content1"
        assert data["files"][1]["filename"] == "file2.txt"
        assert base64.b64decode(data["files"][1]["content"]) == b"content2"

    @pytest.mark.asyncio
    async def test_transfer_files_empty(self, client, mock_node_service):
        """Transfer files returns empty list when no files in range."""
        mock_node_service.get_files_in_range.return_value = []

        response = await client.post(
            "/files/transfer",
            json={"start_key": 0, "end_key": 100},
        )

        assert response.status_code == 200
        assert response.json()["files"] == []

    @pytest.mark.asyncio
    async def test_transfer_files_calls_service_with_correct_range(self, client, mock_node_service):
        """Transfer endpoint passes correct range to service."""
        mock_node_service.get_files_in_range.return_value = []

        await client.post(
            "/files/transfer",
            json={"start_key": 50, "end_key": 150},
        )

        mock_node_service.get_files_in_range.assert_called_once_with(50, 150)
