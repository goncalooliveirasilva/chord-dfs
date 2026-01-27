"""Message types for inter-node communication."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeAddress:
    """Network address of a node."""

    host: str
    port: int

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"


@dataclass(frozen=True)
class NodeInfo:
    """Node identity and address."""

    node_id: int
    address: NodeAddress


@dataclass(frozen=True)
class JoinRequest:
    """Request to join the ring."""

    node_id: int
    address: NodeAddress


@dataclass(frozen=True)
class JoinResponse:
    """Response to join request with successor info."""

    successor_id: int
    successor_address: NodeAddress


@dataclass(frozen=True)
class FindSuccessorRequest:
    """Request to find successor of a key."""

    key: int
    requester_address: NodeAddress


@dataclass(frozen=True)
class FindSuccessorResponse:
    """Response with successor info."""

    successor_id: int
    successor_address: NodeAddress


@dataclass(frozen=True)
class NotifyRequest:
    """Notify a node about its potential predecessor."""

    predecessor_id: int
    predecessor_address: NodeAddress


@dataclass(frozen=True)
class PredecessorResponse:
    """Response with predecessor info."""

    predecessor_id: int | None
    predecessor_address: NodeAddress | None
