"""Abstract storage backend protocol."""

from typing import Protocol


class StorageBackend(Protocol):
    """
    Abstract storage backend for file persistence.

    Implementations of this protocol handle the actual file I/O,
    allowing the Chord node to remain decoupled from storage details.
    """

    async def save(self, filename: str, content: bytes) -> str:
        """Save file content to storage.

        Args:
            filename (str): Name of the file
            content (bytes): File content

        Returns:
            str: Path where the file was saved
        """
        ...

    async def get(self, filename: str) -> bytes | None:
        """Retrieve file content from storage.

        Args:
            filename (str): Name of the file

        Returns:
            bytes | None: File content, or None if not found
        """
        ...

    async def delete(self, filename: str) -> bool:
        """Delete a file from storage.

        Args:
            filename (str): Name of the file

        Returns:
            bool: True if deleted, False if not found
        """
        ...

    async def exists(self, filename: str) -> bool:
        """Check if a file exists in storage.

        Args:
            filename (str): Name of the file

        Returns:
            bool: True if file exists, False otherwise
        """
        ...

    async def list_files(self) -> list[str]:
        """List all files in storage.

        Returns:
            list[str]: List of filenames
        """
        ...
