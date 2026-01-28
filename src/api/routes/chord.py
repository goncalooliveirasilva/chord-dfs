"""Chord DHT protocol routes."""

from fastapi import APIRouter

from src.api.schemas.chord import (
    FindSuccessorRequest,
    FindSuccessorResponse,
    JoinRequest,
    JoinResponse,
    KeepAliveResponse,
    NodeAddressSchema,
    NodeInfoResponse,
    NotifyRequest,
    NotifyResponse,
    PredecessorResponse,
)

router = APIRouter(prefix="/chord", tags=["chord"])


@router.post("/successor", response_model=FindSuccessorResponse)
async def find_successor(request: FindSuccessorRequest) -> FindSuccessorResponse:
    """Find the successor node for a given key.

    Used for routing requests to the responsible node.
    """
    # TODO: Implement with node service
    return FindSuccessorResponse(
        successor_id=0, successor_addr=NodeAddressSchema(host="localhost", port=5000)
    )


@router.get("/predecessor", response_model=PredecessorResponse)
async def get_predecessor() -> PredecessorResponse:
    """Get this node's predecessor.

    Used during stabilization protocol.
    """
    # TODO: Implement with node service
    return PredecessorResponse(
        predecessor_id=None,
        predecessor_addr=None,
    )


@router.post("/notify", response_model=NotifyResponse)
async def notify(request: NotifyRequest) -> NotifyResponse:
    """Notify this node about a potential predecessor.

    Called by nodes that think they might be our predecessor.
    """
    # TODO: Implement with node service
    return NotifyResponse(message="ACK")


@router.post("/join", response_model=JoinResponse)
async def join(request: JoinRequest) -> JoinResponse:
    """Handle a join request from a new node.

    Finds the appropriate successor for the joining node.
    """
    # TODO: Implement with node service
    return JoinResponse(
        successor_id=0, successor_addr=NodeAddressSchema(host="localhost", port=5000)
    )


@router.get("/info", response_model=NodeInfoResponse)
async def get_info() -> NodeInfoResponse:
    """Get full node state information.

    Returns node ID, address, successor, predecessor, and finger table.
    """
    # TODO: Implement with node service
    return NodeInfoResponse(
        id=0,
        address=NodeAddressSchema(host="localhost", port=5000),
        successor_id=0,
        successor_addr=NodeAddressSchema(host="localhost", port=5000),
        predecessor_id=None,
        predecessor_addr=None,
        finger_table=[],
    )


@router.post("/keepalive", response_model=KeepAliveResponse)
async def keep_alive() -> KeepAliveResponse:
    """Health check endpoint for node liveness detection."""
    return KeepAliveResponse(message="alive")
