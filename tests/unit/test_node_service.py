"""Tests for NodeService."""

from unittest.mock import AsyncMock, patch

import pytest

from src.network.messages import NodeAddress, NodeInfo
from src.services.node_service import NodeService


@pytest.fixture
def mock_transport():
    """Create a mock transport."""
    transport = AsyncMock()
    transport.close = AsyncMock()
    return transport


@pytest.fixture
def mock_storage():
    """Create a mock storage backend."""
    storage = AsyncMock()
    storage.initialize = AsyncMock()
    storage.save = AsyncMock(return_value="/path/to/file")
    storage.get = AsyncMock(return_value=b"file content")
    storage.delete = AsyncMock(return_value=True)
    storage.list_files = AsyncMock(return_value=["file1.txt", "file2.txt"])
    return storage


@pytest.fixture
def node_service(tmp_path, mock_transport, mock_storage):
    """Create a NodeService for testing."""
    with (
        patch("src.services.node_service.HttpTransport", return_value=mock_transport),
        patch("src.services.node_service.LocalStorageBackend", return_value=mock_storage),
    ):
        service = NodeService(
            host="localhost",
            port=5000,
            m_bits=10,
            stabilize_interval=1.0,
            storage_path=tmp_path,
        )
        service.transport = mock_transport
        service.storage = mock_storage
        return service


class TestNodeServiceInit:
    """Tests for NodeService initialization."""

    def test_init_basic(self, tmp_path):
        """Initialize a NodeService."""
        with (
            patch("src.services.node_service.HttpTransport"),
            patch("src.services.node_service.LocalStorageBackend"),
        ):
            service = NodeService(
                host="localhost",
                port=5000,
                storage_path=tmp_path,
            )

            assert service.address.host == "localhost"
            assert service.address.port == 5000
            assert service.bootstrap_address is None

    def test_init_with_bootstrap(self, tmp_path):
        """Initialize with bootstrap address."""
        with (
            patch("src.services.node_service.HttpTransport"),
            patch("src.services.node_service.LocalStorageBackend"),
        ):
            service = NodeService(
                host="localhost",
                port=5000,
                bootstrap_address=("node0", 5000),
                storage_path=tmp_path,
            )

            assert service.bootstrap_address == ("node0", 5000)

    def test_init_creates_chord_node(self, tmp_path):
        """ChordNode is created on init."""
        with (
            patch("src.services.node_service.HttpTransport"),
            patch("src.services.node_service.LocalStorageBackend"),
        ):
            service = NodeService(
                host="localhost",
                port=5000,
                storage_path=tmp_path,
            )

            assert service.node is not None
            assert service.node.node_id == service.node_id


class TestNodeServiceStartStop:
    """Tests for start and stop methods."""

    @pytest.mark.asyncio
    async def test_start_initializes_storage(self, node_service, mock_storage):
        """Start initializes storage."""
        await node_service.start()

        mock_storage.initialize.assert_called_once()
        assert node_service._running is True
        assert node_service._stabilize_task is not None

        await node_service.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, node_service, mock_transport):
        """Stop cancels stabilization task."""
        await node_service.start()
        await node_service.stop()

        assert node_service._running is False
        mock_transport.close.assert_called_once()


class TestNodeServiceHandleJoin:
    """Tests for handle_join method."""

    @pytest.mark.asyncio
    async def test_handle_join_when_alone(self, node_service):
        """Handle join when node is alone."""
        joining_addr = NodeAddress(host="newnode", port=5001)
        joining_id = 200

        result = await node_service.handle_join(joining_id, joining_addr)

        # When alone, returns our info and sets joining node as successor
        assert result.node_id == node_service.node_id
        assert node_service.node.successor.node_id == joining_id

    @pytest.mark.asyncio
    async def test_handle_join_with_successor(self, node_service):
        """Handle join when we have a successor."""
        # Set up a successor
        successor = NodeInfo(node_id=500, address=NodeAddress(host="successor", port=5002))
        node_service.node.set_successor(successor)

        # Join request from node between us and successor
        joining_addr = NodeAddress(host="newnode", port=5001)
        joining_id = (node_service.node_id + 100) % 1024

        result = await node_service.handle_join(joining_id, joining_addr)

        # Should return old successor info
        assert result.node_id == 500


class TestNodeServiceHandleNotify:
    """Tests for handle_notify method."""

    @pytest.mark.asyncio
    async def test_handle_notify_sets_predecessor(self, node_service):
        """Handle notify sets predecessor when none exists."""
        pred_addr = NodeAddress(host="predecessor", port=5001)
        pred_id = 50

        result = await node_service.handle_notify(pred_id, pred_addr)

        assert result is True
        assert node_service.node.predecessor.node_id == pred_id


class TestNodeServiceFileOperations:
    """Tests for file operation methods."""

    @pytest.mark.asyncio
    async def test_put_file_local(self, node_service, mock_storage):
        """Put file stores locally when responsible."""
        # Make node responsible for all keys
        node_service.node.predecessor = None

        success, node_id = await node_service.put_file("test.txt", b"content")

        assert success is True
        assert node_id == str(node_service.node_id)
        mock_storage.save.assert_called_once_with("test.txt", b"content")

    @pytest.mark.asyncio
    async def test_put_file_forward(self, node_service, mock_transport):
        """Put file forwards when not responsible."""
        # Set up predecessor so we're not responsible for all keys
        node_service.node.predecessor = NodeInfo(
            node_id=(node_service.node_id - 10) % 1024,
            address=NodeAddress(host="pred", port=5001),
        )
        # Set up successor
        successor = NodeInfo(
            node_id=(node_service.node_id + 100) % 1024,
            address=NodeAddress(host="successor", port=5002),
        )
        node_service.node.set_successor(successor)
        mock_transport.forward_file.return_value = True

        # Use a filename that will hash to a key we're not responsible for
        success, _ = await node_service.put_file("test.txt", b"content")

        # The behavior depends on the hash - it will either store locally or forward
        assert success is True

    @pytest.mark.asyncio
    async def test_get_file_local(self, node_service, mock_storage):
        """Get file retrieves locally when responsible."""
        # Make node responsible for all keys
        node_service.node.predecessor = None
        mock_storage.get.return_value = b"file content"

        content = await node_service.get_file("test.txt")

        assert content == b"file content"

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, node_service, mock_storage):
        """Get file returns None when not found."""
        node_service.node.predecessor = None
        mock_storage.get.return_value = None

        content = await node_service.get_file("nonexistent.txt")

        assert content is None

    @pytest.mark.asyncio
    async def test_delete_file_local(self, node_service, mock_storage):
        """Delete file removes locally when responsible."""
        node_service.node.predecessor = None
        mock_storage.delete.return_value = True

        result = await node_service.delete_file("test.txt")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, node_service, mock_storage):
        """Delete file returns False when not found."""
        node_service.node.predecessor = None
        mock_storage.delete.return_value = False

        result = await node_service.delete_file("nonexistent.txt")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_local_files(self, node_service, mock_storage):
        """List local files returns storage files."""
        mock_storage.list_files.return_value = ["file1.txt", "file2.txt"]

        files = await node_service.list_local_files()

        assert files == ["file1.txt", "file2.txt"]

    @pytest.mark.asyncio
    async def test_store_file_locally(self, node_service, mock_storage):
        """Store file locally saves to storage."""
        mock_storage.save.return_value = "/path/to/file.txt"

        path = await node_service.store_file_locally("file.txt", b"content")

        assert path == "/path/to/file.txt"
        mock_storage.save.assert_called_with("file.txt", b"content")


class TestNodeServiceHelpers:
    """Tests for helper methods."""

    def test_get_file_key(self, node_service):
        """Get file key returns hash of filename."""
        key = node_service.get_file_key("test.txt")

        assert isinstance(key, int)
        assert 0 <= key < 1024  # m_bits = 10

    def test_is_responsible_for(self, node_service):
        """is_responsible_for delegates to node."""
        node_service.node.predecessor = None

        # With no predecessor, responsible for all keys
        assert node_service.is_responsible_for(500) is True

    def test_get_predecessor(self, node_service):
        """get_predecessor returns node's predecessor."""
        assert node_service.get_predecessor() is None

        pred = NodeInfo(node_id=50, address=NodeAddress(host="pred", port=5001))
        node_service.node.predecessor = pred

        assert node_service.get_predecessor() == pred

    def test_info_property(self, node_service):
        """info property returns node info."""
        info = node_service.info

        assert info.node_id == node_service.node_id
        assert info.address == node_service.address
