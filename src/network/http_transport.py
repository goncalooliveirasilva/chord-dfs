"""HTTP transport implementation."""

import base64
import logging

import httpx

from src.network.messages import (
    FindSuccessorResponse,
    JoinResponse,
    NodeAddress,
    PredecessorResponse,
)
from src.network.protocol import Transport

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0


class HttpTransport(Transport):
    """HTTP-based tranport for Chord inter-node communication.

    Uses httpx.AsyncClient to make async HTTP requests to other nodes.
    Implements the Transport protocol.
    """

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        """Initialize the HTTP transport.

        Args:
            timeout (float, optional): timeout in seconds. Defaults to DEFAULT_TIMEOUT.
        """
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _url(self, target: NodeAddress, path: str) -> str:
        """Build URL for a target node."""
        return f"http://{target.host}:{target.port}{path}"

    async def join(
        self, target: NodeAddress, node_id: int, node_address: NodeAddress
    ) -> JoinResponse:
        """Send join request to a node."""
        client = await self._get_client()
        url = self._url(target, "/chord/join")

        try:
            response = await client.post(
                url,
                json={
                    "id": node_id,
                    "address": {"host": node_address.host, "port": node_address.port},
                },
            )
            response.raise_for_status()
            data = response.json()
            return JoinResponse(
                successor_id=data["successor_id"],
                successor_address=NodeAddress(
                    host=data["successor_addr"]["host"],
                    port=data["successor_addr"]["port"],
                ),
            )
        except httpx.HTTPError as e:
            logger.error("Join request to %s failed: %s", target, e)
            raise

    async def find_successor(
        self, target: NodeAddress, key: int, requester_address: NodeAddress
    ) -> FindSuccessorResponse:
        """Request successor of a key from a node."""
        client = await self._get_client()
        url = self._url(target, "/chord/successor")

        try:
            response = await client.post(
                url,
                json={
                    "id": key,
                    "requester": {"host": requester_address.host, "port": requester_address.port},
                },
            )
            response.raise_for_status()
            data = response.json()
            return FindSuccessorResponse(
                successor_id=data["successor_id"],
                successor_address=NodeAddress(
                    host=data["successor_addr"]["host"],
                    port=data["successor_addr"]["port"],
                ),
            )
        except httpx.HTTPError as e:
            logger.error("Find successor request to %s failed: %s", target, e)
            raise

    async def notify(
        self, target: NodeAddress, predecessor_id: int, predecessor_address: NodeAddress
    ) -> bool:
        """Notify a node about its potential predecessor."""
        client = await self._get_client()
        url = self._url(target, "/chord/notify")

        try:
            response = await client.post(
                url,
                json={
                    "predecessor_id": predecessor_id,
                    "predecessor_addr": {
                        "host": predecessor_address.host,
                        "port": predecessor_address.port,
                    },
                },
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error("Notify request to %s failed: %s", target, e)
            return False

    async def get_predecessor(self, target: NodeAddress) -> PredecessorResponse:
        """Get predecessor info from a node."""
        client = await self._get_client()
        url = self._url(target, "/chord/predecessor")

        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            pred_addr = None
            if data.get("predecessor_addr"):
                pred_addr = NodeAddress(
                    host=data["predecessor_addr"]["host"],
                    port=data["predecessor_addr"]["port"],
                )
            return PredecessorResponse(
                predecessor_id=data.get("predecessor_id"),
                predecessor_address=pred_addr,
            )
        except httpx.HTTPError as e:
            logger.error("Get predecessor request to %s failed: %s", target, e)
            raise

    async def forward_file(self, target: NodeAddress, filename: str, content: bytes) -> bool:
        """Forward a file to the responsible node."""
        client = await self._get_client()
        url = self._url(target, "/files/forward")

        try:
            files = {"file": (filename, content)}
            response = await client.post(url, files=files)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error("Forward file to %s failed: %s", target, e)
            return False

    async def get_file(self, target: NodeAddress, filename: str) -> bytes | None:
        """Retrieve a file from a node."""
        client = await self._get_client()
        url = self._url(target, f"/files/{filename}")

        try:
            response = await client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as e:
            logger.error("Get file from %s failed: %s", target, e)
            return None

    async def delete_file(self, target: NodeAddress, filename: str) -> bool:
        """Delete a file from a node."""
        client = await self._get_client()
        url = self._url(target, f"/files/{filename}")

        try:
            response = await client.delete(url)
            if response.status_code == 404:
                return False
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error("Delete file from %s failed: %s", target, e)
            return False

    async def ping(self, target: NodeAddress) -> bool:
        """Check if a node is alive."""
        client = await self._get_client()
        url = self._url(target, "/chord/keepalive")

        try:
            response = await client.post(url)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def request_files_in_range(
        self, target: NodeAddress, start_key: int, end_key: int
    ) -> list[tuple[str, bytes]]:
        """Request files in a key range from a nodefor migration.

        Args:
            target (NodeAddress): Node to request files from
            start_key (int): Start of range (exclusive)
            end_key (int): End of range (inclusive)

        Returns:
            list[tuple[str, bytes]]: List of (filename, content) tuples
        """
        client = await self._get_client()
        url = self._url(target, "/files/transfer")

        try:
            response = await client.post(
                url,
                json={"start_key": start_key, "end_key": end_key},
            )
            response.raise_for_status()
            data = response.json()

            return [(f["filename"], base64.b64decode(f["content"])) for f in data.get("files", [])]
        except httpx.HTTPError as e:
            logger.error("Request files in range from %s failed: %s", target, e)
            return []
