"""API tests for Chord protocol endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import create_app
from src.config import Settings
from src.network.messages import NodeAddress, NodeInfo


@pytest.fixture
def mock_node_service():
    """Create a mock NodeService."""
    service = AsyncMock()
    service.node_id = 100
    service.address = NodeAddress(host="localhost", port=5000)
    service.start = AsyncMock()
    service.stop = AsyncMock()
    service.info = NodeInfo(
        node_id=100,
        address=NodeAddress(host="localhost", port=5000),
    )

    # Mock the internal node
    mock_node = MagicMock()
    mock_node.successor = NodeInfo(
        node_id=200,
        address=NodeAddress(host="localhost", port=5001),
    )
    mock_node.predecessor = None

    # Mock finger table
    mock_finger_table = MagicMock()
    mock_finger_table.get_node_ids.return_value = [200] * 10
    mock_node.finger_table = mock_finger_table

    service.node = mock_node

    # Mock methods
    service.is_responsible_for = MagicMock(return_value=True)
    service.get_forward_target = MagicMock(
        return_value=NodeInfo(
            node_id=200,
            address=NodeAddress(host="localhost", port=5001),
        )
    )
    service.get_predecessor = MagicMock(return_value=None)
    service.handle_notify = AsyncMock(return_value=True)
    service.handle_join = AsyncMock(
        return_value=NodeInfo(
            node_id=200,
            address=NodeAddress(host="localhost", port=5001),
        )
    )

    return service


@pytest.fixture
def test_settings(tmp_path):
    """Create test settings."""
    return Settings(
        host="localhost",
        port=5000,
        storage_path=str(tmp_path),
    )


@pytest.fixture
async def client(test_settings, mock_node_service):
    """Create a test client with mocked NodeService."""
    with patch("src.api.app.NodeService", return_value=mock_node_service):
        app = create_app(settings=test_settings)
        app.state.node_service = mock_node_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client


class TestFindSuccessor:
    """Tests for POST /chord/successor endpoint."""

    @pytest.mark.asyncio
    async def test_find_successor_responsible(self, client, mock_node_service):
        """Find successor when this node is responsible."""
        mock_node_service.is_responsible_for.return_value = True

        response = await client.post(
            "/chord/successor",
            json={
                "id": 150,
                "requester": {"host": "requester", "port": 5002},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["successor_id"] == 100
        assert data["successor_addr"]["host"] == "localhost"
        assert data["successor_addr"]["port"] == 5000

    @pytest.mark.asyncio
    async def test_find_successor_forward(self, client, mock_node_service):
        """Find successor when forwarding is needed."""
        mock_node_service.is_responsible_for.return_value = False
        mock_node_service.get_forward_target.return_value = NodeInfo(
            node_id=300,
            address=NodeAddress(host="forward", port=5003),
        )

        response = await client.post(
            "/chord/successor",
            json={
                "id": 350,
                "requester": {"host": "requester", "port": 5002},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["successor_id"] == 300
        assert data["successor_addr"]["host"] == "forward"


class TestGetPredecessor:
    """Tests for GET /chord/predecessor endpoint."""

    @pytest.mark.asyncio
    async def test_get_predecessor_none(self, client, mock_node_service):
        """Get predecessor when none exists."""
        mock_node_service.get_predecessor.return_value = None

        response = await client.get("/chord/predecessor")

        assert response.status_code == 200
        data = response.json()
        assert data["predecessor_id"] is None
        assert data["predecessor_addr"] is None

    @pytest.mark.asyncio
    async def test_get_predecessor_exists(self, client, mock_node_service):
        """Get predecessor when one exists."""
        mock_node_service.get_predecessor.return_value = NodeInfo(
            node_id=50,
            address=NodeAddress(host="predecessor", port=5001),
        )

        response = await client.get("/chord/predecessor")

        assert response.status_code == 200
        data = response.json()
        assert data["predecessor_id"] == 50
        assert data["predecessor_addr"]["host"] == "predecessor"


class TestNotify:
    """Tests for POST /chord/notify endpoint."""

    @pytest.mark.asyncio
    async def test_notify_success(self, client, mock_node_service):
        """Notify endpoint returns ACK."""
        response = await client.post(
            "/chord/notify",
            json={
                "predecessor_id": 50,
                "predecessor_addr": {"host": "notifier", "port": 5001},
            },
        )

        assert response.status_code == 200
        assert response.json()["message"] == "ACK"
        mock_node_service.handle_notify.assert_called_once()


class TestJoin:
    """Tests for POST /chord/join endpoint."""

    @pytest.mark.asyncio
    async def test_join_success(self, client, mock_node_service):
        """Join returns successor info."""
        mock_node_service.handle_join.return_value = NodeInfo(
            node_id=200,
            address=NodeAddress(host="successor", port=5001),
        )

        response = await client.post(
            "/chord/join",
            json={
                "id": 150,
                "address": {"host": "newnode", "port": 5002},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["successor_id"] == 200
        assert data["successor_addr"]["host"] == "successor"


class TestGetInfo:
    """Tests for GET /chord/info endpoint."""

    @pytest.mark.asyncio
    async def test_get_info_no_predecessor(self, client, mock_node_service):
        """Get info when no predecessor."""
        mock_node_service.node.predecessor = None

        response = await client.get("/chord/info")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 100
        assert data["address"]["host"] == "localhost"
        assert data["successor_id"] == 200
        assert data["predecessor_id"] is None
        assert "finger_table" in data

    @pytest.mark.asyncio
    async def test_get_info_with_predecessor(self, client, mock_node_service):
        """Get info with predecessor."""
        mock_node_service.node.predecessor = NodeInfo(
            node_id=50,
            address=NodeAddress(host="predecessor", port=5001),
        )

        response = await client.get("/chord/info")

        assert response.status_code == 200
        data = response.json()
        assert data["predecessor_id"] == 50
        assert data["predecessor_addr"]["host"] == "predecessor"


class TestKeepAlive:
    """Tests for POST /chord/keepalive endpoint."""

    @pytest.mark.asyncio
    async def test_keepalive(self, client):
        """Keep alive returns alive message."""
        response = await client.post("/chord/keepalive")

        assert response.status_code == 200
        assert response.json()["message"] == "alive"
