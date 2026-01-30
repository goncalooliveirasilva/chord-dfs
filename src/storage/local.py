"""Local file system storage backend using aiofiles."""

import logging
from pathlib import Path

import aiofiles
import aiofiles.os

from src.storage.protocol import StorageBackend

logger = logging.getLogger(__name__)


class LocalStorageBackend(StorageBackend):
    """Local file system storage implementation.

    Stores files in a directory on the local file system using async I/O.
    Implements the StorageBackend protocol.
    """

    def __init__(self, base_path: str | Path = "/app/storage") -> None:
        """Initialize the local storage backend.

        Args:
            base_path (str | Path, optional): Directory to store files in.
                Defaults to "/app/storage".
        """
        self.base_path = Path(base_path)

    async def initialize(self) -> None:
        """Create the storage directory if it doesn't exist."""
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info("Created storage directory: %s", self.base_path)

    def _file_path(self, filename: str) -> Path:
        """Get the full path for a file."""
        # Sanitize filename to prevent path traversal"
        safe_name = Path(filename).name
        return self.base_path / safe_name

    async def save(self, filename: str, content: bytes) -> str:
        """Save file content to storage."""
        file_path = self._file_path(filename)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        logger.debug("Saved file: %s (%d bytes)", filename, len(content))
        return str(file_path)

    async def get(self, filename: str) -> bytes | None:
        """Retreive file content from storage."""
        file_path = self._file_path(filename)

        if not file_path.exists():
            return None

        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()

        logger.debug("Retrieve file: %s (%d bytes)", filename, len(content))
        return content

    async def delete(self, filename: str) -> bool:
        """Delete a file from storage."""
        file_path = self._file_path(filename)

        if not file_path.exists():
            return False

        await aiofiles.os.remove(file_path)
        logger.debug("Deleted file: %s", filename)
        return True

    async def exists(self, filename: str) -> bool:
        """Check if a file exists in storage."""
        file_path = self._file_path(filename)
        return file_path.exists()

    async def list_files(self) -> list[str]:
        """List all files in storage."""
        if not self.base_path.exists():
            return []
        return [f.name for f in self.base_path.iterdir() if f.is_file()]
