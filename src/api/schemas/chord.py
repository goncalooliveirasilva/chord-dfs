"""Pydantic schemas for Chord DHT protocol operations."""

from pydantic import BaseModel


class NodeAddressSchema(BaseModel):
    """Network address of a node."""

    host: str
    port: int


class FindSuccessorRequest(BaseModel):
    """Request to find successor for a key."""

    id: int
    requester: NodeAddressSchema


class FindSuccessorResponse(BaseModel):
    """Response with successor information."""

    successor_id: int
    successor_addr: NodeAddressSchema


class PredecessorResponse(BaseModel):
    """Response with predecessor information."""

    predecessor_id: int | None
    predecessor_addr: NodeAddressSchema | None


class NotifyRequest(BaseModel):
    """Notify a node about a potential predecessor."""

    predecessor_id: int
    predecessor_addr: NodeAddressSchema


class NotifyResponse(BaseModel):
    """Response to notify request."""

    message: str


class JoinRequest(BaseModel):
    """Request to join the ring."""

    id: int
    address: NodeAddressSchema


class JoinResponse(BaseModel):
    """Response to join request with successor info."""

    successor_id: int
    successor_addr: NodeAddressSchema


class NodeInfoResponse(BaseModel):
    """Full node state information."""

    id: int
    address: NodeAddressSchema
    successor_id: int
    successor_addr: NodeAddressSchema
    predecessor_id: int | None
    predecessor_addr: NodeAddressSchema | None
    finger_table: list[int]


class KeepAliveResponse(BaseModel):
    """Response to keep-alive request."""

    message: str
