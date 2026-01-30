"""Shared pytest fixtures."""

import pytest

from src.network.messages import NodeAddress, NodeInfo


@pytest.fixture
def node_address() -> NodeAddress:
    """Create a test node address."""
    return NodeAddress(host="localhost", port=5000)


@pytest.fixture
def other_address() -> NodeAddress:
    """Create another test node address."""
    return NodeAddress(host="localhost", port=5001)


@pytest.fixture
def node_info(node_address: NodeAddress) -> NodeInfo:
    """Create a test node info."""
    return NodeInfo(node_id=100, address=node_address)


@pytest.fixture
def other_node_info(other_address: NodeAddress) -> NodeInfo:
    """Create another test node info."""
    return NodeInfo(node_id=200, address=other_address)
