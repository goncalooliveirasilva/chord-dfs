"""Abstract transport protocol for inter-node communication."""

from typing import Protocol

from src.network.messages import (
    FindSuccessorResponse,
    JoinResponse,
    NodeAddress,
    PredecessorResponse,
)


class Transport(Protocol):
    """Abstract network transport for Chord inter-node communication."""

    async def join(
        self, target: NodeAddress, node_id: int, node_address: NodeAddress
    ) -> JoinResponse:
        """Send join request to a node."""
        ...

    async def find_successor(
        self,
        target: NodeAddress,
        key: int,
        requester_address: NodeAddress,
    ) -> FindSuccessorResponse:
        """Request successor of a key from a node."""
        ...

    async def notify(
        self,
        target: NodeAddress,
        predecessor_id: int,
        predecessor_address: NodeAddress,
    ) -> bool:
        """Notify a node about its potential predecessor."""
        ...

    async def get_predecessor(
        self,
        target: NodeAddress,
    ) -> PredecessorResponse:
        """Get predecessor info from a node."""
        ...

    async def forward_file(
        self,
        target: NodeAddress,
        filename: str,
        content: bytes,
    ) -> bool:
        """Forward a file to the responsible node."""
        ...

    async def get_file(
        self,
        target: NodeAddress,
        filename: str,
    ) -> bytes | None:
        """Retrieve a file from a node."""
        ...

    async def delete_file(
        self,
        target: NodeAddress,
        filename: str,
    ) -> bool:
        """Delete a file from a node."""
        ...

    async def ping(self, target: NodeAddress) -> bool:
        """Check if a node is alive (failure detection)."""
        ...
