"""Chord DHT protocol routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

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
from src.network.messages import NodeAddress
from src.services.node_service import NodeService

router = APIRouter(prefix="/chord", tags=["chord"])


def get_node_service(request: Request) -> NodeService:
    """Dependency to get NodeService from app state."""
    return request.app.state.node_service


NodeServiceDep = Annotated[NodeService, Depends(get_node_service)]


@router.post("/successor", response_model=FindSuccessorResponse)
async def find_successor(
    request: FindSuccessorRequest, node_service: NodeServiceDep
) -> FindSuccessorResponse:
    """Find the successor node for a given key.

    Used for routing requests to the responsible node.
    """
    # Check if we are responsible for this key
    if node_service.is_responsible_for(request.id):
        info = node_service.info
        return FindSuccessorResponse(
            successor_id=info.node_id,
            successor_addr=NodeAddressSchema(
                host=info.address.host,
                port=info.address.port,
            ),
        )

    # Get the node to forward to
    target = node_service.get_forward_target(request.id)
    return FindSuccessorResponse(
        successor_id=target.node_id,
        successor_addr=NodeAddressSchema(
            host=target.address.host,
            port=target.address.port,
        ),
    )


@router.get("/predecessor", response_model=PredecessorResponse)
async def get_predecessor(node_service: NodeServiceDep) -> PredecessorResponse:
    """Get this node's predecessor.

    Used during stabilization protocol.
    """
    pred = node_service.get_predecessor()
    if pred is None:
        return PredecessorResponse(
            predecessor_id=None,
            predecessor_addr=None,
        )
    return PredecessorResponse(
        predecessor_id=pred.node_id,
        predecessor_addr=NodeAddressSchema(
            host=pred.address.host,
            port=pred.address.port,
        ),
    )


@router.post("/notify", response_model=NotifyResponse)
async def notify(request: NotifyRequest, node_service: NodeServiceDep) -> NotifyResponse:
    """Notify this node about a potential predecessor.

    Called by nodes that think they might be our predecessor.
    """
    node_service.handle_notify(
        predecessor_id=request.predecessor_id,
        predecessor_address=NodeAddress(
            host=request.predecessor_addr.host,
            port=request.predecessor_addr.port,
        ),
    )
    return NotifyResponse(message="ACK")


@router.post("/join", response_model=JoinResponse)
async def join(request: JoinRequest, node_service: NodeServiceDep) -> JoinResponse:
    """Handle a join request from a new node.

    Finds the appropriate successor for the joining node.
    """
    successor = await node_service.handle_join(
        joining_id=request.id,
        joining_address=NodeAddress(
            host=request.address.host,
            port=request.address.port,
        ),
    )
    return JoinResponse(
        successor_id=successor.node_id,
        successor_addr=NodeAddressSchema(
            host=successor.address.host,
            port=successor.address.port,
        ),
    )


@router.get("/info", response_model=NodeInfoResponse)
async def get_info(node_service: NodeServiceDep) -> NodeInfoResponse:
    """Get full node state information.

    Returns node ID, address, successor, predecessor, and finger table.
    """
    info = node_service.info
    node = node_service.node
    pred = node.predecessor

    return NodeInfoResponse(
        id=info.node_id,
        address=NodeAddressSchema(
            host=info.address.host,
            port=info.address.port,
        ),
        successor_id=node.successor.node_id,
        successor_addr=NodeAddressSchema(
            host=node.successor.address.host,
            port=node.successor.address.port,
        ),
        predecessor_id=pred.node_id if pred else None,
        predecessor_addr=(
            NodeAddressSchema(
                host=pred.address.host,
                port=pred.address.port,
            )
            if pred
            else None
        ),
        finger_table=node.finger_table.get_node_ids(),
    )


@router.post("/keepalive", response_model=KeepAliveResponse)
async def keep_alive() -> KeepAliveResponse:
    """Health check endpoint for node liveness detection."""
    return KeepAliveResponse(message="alive")
