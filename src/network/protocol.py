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
        """Send join request to a node.

        Args:
            target (NodeAddress): Node to send the join request to
            node_id (int): ID of the node requesting to join
            node_address (NodeAddress): Address of the node requesting to join

        Returns:
            JoinResponse: Successor information for the joining node
        """
        ...

    async def find_successor(
        self,
        target: NodeAddress,
        key: int,
        requester_address: NodeAddress,
    ) -> FindSuccessorResponse:
        """Request successor of a key from a node.

        Args:
            target (NodeAddress): Node to query
            key (int): Key to find successor for
            requester_address (NodeAddress): Address of the requesting node

        Returns:
            FindSuccessorResponse: Successor information for the key
        """
        ...

    async def notify(
        self,
        target: NodeAddress,
        predecessor_id: int,
        predecessor_address: NodeAddress,
    ) -> bool:
        """Notify a node about its potential predecessor.

        Args:
            target (NodeAddress): Node to notify
            predecessor_id (int): ID of the potential predecessor
            predecessor_address (NodeAddress): Address of the potential predecessor

        Returns:
            bool: True if notification was acknowledged
        """
        ...

    async def get_predecessor(
        self,
        target: NodeAddress,
    ) -> PredecessorResponse:
        """Get predecessor info from a node.

        Args:
            target (NodeAddress): Node to query

        Returns:
            PredecessorResponse: Predecessor information of the target node
        """
        ...

    async def forward_file(
        self,
        target: NodeAddress,
        filename: str,
        content: bytes,
    ) -> bool:
        """Forward a file to the responsible node.

        Args:
            target (NodeAddress): Node to forward the file to
            filename (str): Name of the file
            content (bytes): File content

        Returns:
            bool: True if file was successfully forwarded
        """
        ...

    async def get_file(
        self,
        target: NodeAddress,
        filename: str,
    ) -> bytes | None:
        """Retrieve a file from a node.

        Args:
            target (NodeAddress): Node to retrieve the file from
            filename (str): Name of the file

        Returns:
            bytes | None: File content, or None if not found
        """
        ...

    async def delete_file(
        self,
        target: NodeAddress,
        filename: str,
    ) -> bool:
        """Delete a file from a node.

        Args:
            target (NodeAddress): Node to delete the file from
            filename (str): Name of the file

        Returns:
            bool: True if deleted, False if not found
        """
        ...

    async def ping(self, target: NodeAddress) -> bool:
        """Check if a node is alive (failure detection).

        Args:
            target (NodeAddress): Node to ping

        Returns:
            bool: True if node is alive, False otherwise
        """
        ...
