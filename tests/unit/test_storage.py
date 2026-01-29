"""Tests for LocalStorageBackend."""

import pytest

from src.storage.local import LocalStorageBackend


@pytest.fixture
def storage_backend(tmp_path):
    """Create a LocalStorageBackend with a temporary directory."""
    return LocalStorageBackend(base_path=tmp_path)


class TestLocalStorageBackendInit:
    """Tests for LocalStorageBackend initialization."""

    def test_init_with_path(self, tmp_path):
        """Initialize with a specific path."""
        backend = LocalStorageBackend(base_path=tmp_path)
        assert backend.base_path == tmp_path

    def test_init_default_path(self):
        """Initialize with default path."""
        backend = LocalStorageBackend()
        assert str(backend.base_path) == "/app/storage"


class TestLocalStorageBackendInitialize:
    """Tests for initialize method."""

    @pytest.mark.asyncio
    async def test_initialize_creates_directory(self, tmp_path):
        """Initialize creates the storage directory."""
        storage_path = tmp_path / "new_storage"
        backend = LocalStorageBackend(base_path=storage_path)

        assert not storage_path.exists()
        await backend.initialize()
        assert storage_path.exists()

    @pytest.mark.asyncio
    async def test_initialize_existing_directory(self, tmp_path):
        """Initialize works with existing directory."""
        backend = LocalStorageBackend(base_path=tmp_path)
        await backend.initialize()
        assert tmp_path.exists()


class TestLocalStorageBackendSave:
    """Tests for save method."""

    @pytest.mark.asyncio
    async def test_save_file(self, storage_backend, tmp_path):
        """Save a file to storage."""
        await storage_backend.initialize()

        path = await storage_backend.save("test.txt", b"hello world")

        assert path == str(tmp_path / "test.txt")
        assert (tmp_path / "test.txt").exists()
        assert (tmp_path / "test.txt").read_bytes() == b"hello world"

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(self, storage_backend, tmp_path):
        """Save overwrites existing file."""
        await storage_backend.initialize()

        await storage_backend.save("test.txt", b"first")
        await storage_backend.save("test.txt", b"second")

        assert (tmp_path / "test.txt").read_bytes() == b"second"

    @pytest.mark.asyncio
    async def test_save_sanitizes_path_traversal(self, storage_backend, tmp_path):
        """Save sanitizes path traversal attempts."""
        await storage_backend.initialize()

        path = await storage_backend.save("../../../etc/passwd", b"malicious")

        # Should be saved as just "passwd" in base_path
        assert "passwd" in path
        assert (tmp_path / "passwd").exists()


class TestLocalStorageBackendGet:
    """Tests for get method."""

    @pytest.mark.asyncio
    async def test_get_existing_file(self, storage_backend, tmp_path):
        """Get an existing file."""
        await storage_backend.initialize()
        (tmp_path / "test.txt").write_bytes(b"hello world")

        content = await storage_backend.get("test.txt")

        assert content == b"hello world"

    @pytest.mark.asyncio
    async def test_get_nonexistent_file(self, storage_backend):
        """Get returns None for nonexistent file."""
        await storage_backend.initialize()

        content = await storage_backend.get("nonexistent.txt")

        assert content is None

    @pytest.mark.asyncio
    async def test_get_binary_file(self, storage_backend, tmp_path):
        """Get a binary file."""
        await storage_backend.initialize()
        binary_content = bytes(range(256))
        (tmp_path / "binary.bin").write_bytes(binary_content)

        content = await storage_backend.get("binary.bin")

        assert content == binary_content


class TestLocalStorageBackendDelete:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, storage_backend, tmp_path):
        """Delete an existing file."""
        await storage_backend.initialize()
        (tmp_path / "test.txt").write_bytes(b"hello")

        result = await storage_backend.delete("test.txt")

        assert result is True
        assert not (tmp_path / "test.txt").exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage_backend):
        """Delete returns False for nonexistent file."""
        await storage_backend.initialize()

        result = await storage_backend.delete("nonexistent.txt")

        assert result is False


class TestLocalStorageBackendExists:
    """Tests for exists method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true(self, storage_backend, tmp_path):
        """Exists returns True for existing file."""
        await storage_backend.initialize()
        (tmp_path / "test.txt").write_bytes(b"hello")

        result = await storage_backend.exists("test.txt")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false(self, storage_backend):
        """Exists returns False for nonexistent file."""
        await storage_backend.initialize()

        result = await storage_backend.exists("nonexistent.txt")

        assert result is False


class TestLocalStorageBackendListFiles:
    """Tests for list_files method."""

    @pytest.mark.asyncio
    async def test_list_files_empty(self, storage_backend):
        """List files returns empty list for empty storage."""
        await storage_backend.initialize()

        files = await storage_backend.list_files()

        assert files == []

    @pytest.mark.asyncio
    async def test_list_files_multiple(self, storage_backend, tmp_path):
        """List files returns all files."""
        await storage_backend.initialize()
        (tmp_path / "file1.txt").write_bytes(b"1")
        (tmp_path / "file2.txt").write_bytes(b"2")
        (tmp_path / "file3.txt").write_bytes(b"3")

        files = await storage_backend.list_files()

        assert sorted(files) == ["file1.txt", "file2.txt", "file3.txt"]

    @pytest.mark.asyncio
    async def test_list_files_excludes_directories(self, storage_backend, tmp_path):
        """List files excludes directories."""
        await storage_backend.initialize()
        (tmp_path / "file.txt").write_bytes(b"1")
        (tmp_path / "subdir").mkdir()

        files = await storage_backend.list_files()

        assert files == ["file.txt"]

    @pytest.mark.asyncio
    async def test_list_files_nonexistent_directory(self, tmp_path):
        """List files returns empty for nonexistent directory."""
        backend = LocalStorageBackend(base_path=tmp_path / "nonexistent")

        files = await backend.list_files()

        assert files == []
