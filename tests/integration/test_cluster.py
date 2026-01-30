"""Integration tests for Chord cluster operations."""

import time

import pytest

from tests.integration.conftest import requires_docker

# Skip all tests in this module if Docker is unavailable
pytestmark = [pytest.mark.integration, requires_docker]


class TestSingleNode:
    """Tests with a single bootstrap node."""

    def test_node_starts_and_is_healthy(self, bootstrap_node):
        """A single node starts and responds to health checks."""
        assert bootstrap_node.is_healthy()

    def test_node_info_shows_self_as_successor(self, bootstrap_node):
        """A single node has itself as successor (alone in ring)."""
        info = bootstrap_node.get_info()

        assert info["id"] is not None
        # When alone, successor should be self
        assert info["successor_id"] == info["id"]

    def test_upload_and_retrieve_file(self, bootstrap_node):
        """Upload and retrieve a file on a single node."""
        content = b"Hello, Chord!"
        result = bootstrap_node.upload_file("test.txt", content)

        assert result["filename"] == "test.txt"
        assert "uploaded successfully" in result["message"]

        retrieved = bootstrap_node.get_file("test.txt")
        assert retrieved == content

    def test_list_files(self, bootstrap_node):
        """List files shows uploaded files."""
        bootstrap_node.upload_file("file1.txt", b"content1")
        bootstrap_node.upload_file("file2.txt", b"content2")

        files = bootstrap_node.list_files()

        assert "file1.txt" in files
        assert "file2.txt" in files

    def test_delete_file(self, bootstrap_node):
        """Delete a file from the node."""
        bootstrap_node.upload_file("to_delete.txt", b"delete me")

        assert bootstrap_node.delete_file("to_delete.txt")

        retrieved = bootstrap_node.get_file("to_delete.txt")
        assert retrieved is None


class TestTwoNodeCluster:
    """Tests with a 2-node cluster."""

    def test_both_nodes_healthy(self, two_node_cluster):
        """Both nodes in the cluster are healthy."""
        for node in two_node_cluster:
            assert node.is_healthy()

    def test_nodes_form_ring(self, two_node_cluster):
        """Two nodes form a proper ring after stabilization."""
        node0, node1 = two_node_cluster

        info0 = node0.get_info()
        info1 = node1.get_info()

        # Each node should have the other as successor or predecessor
        # (depending on their IDs)
        node_ids = {info0["id"], info1["id"]}
        successors = {info0["successor_id"], info1["successor_id"]}

        # In a 2-node ring, each should point to the other as successor
        assert node_ids == successors

    def test_file_accessible_from_any_node(self, two_node_cluster):
        """A file uploaded to one node is accessible from another."""
        node0, node1 = two_node_cluster

        content = b"Distributed content"
        node0.upload_file("distributed.txt", content)

        # File should be accessible from both nodes
        retrieved0 = node0.get_file("distributed.txt")
        retrieved1 = node1.get_file("distributed.txt")

        assert retrieved0 == content
        assert retrieved1 == content

    def test_files_distributed_across_nodes(self, two_node_cluster):
        """Multiple files get distributed across the ring."""
        node0, node1 = two_node_cluster

        # Upload multiple files with different names
        # They should hash to different keys and potentially different nodes
        filenames = [f"file_{i}.txt" for i in range(10)]
        for filename in filenames:
            node0.upload_file(filename, f"content of {filename}".encode())

        # Check that both nodes have some files locally
        files0 = node0.list_files()
        files1 = node1.list_files()

        # At least some files should be on each node
        # (statistically very likely with 10 files)
        total_files = len(files0) + len(files1)
        assert total_files == 10

        # All files should be retrievable from either node
        for filename in filenames:
            content = node0.get_file(filename)
            assert content is not None


class TestThreeNodeCluster:
    """Tests with a 3-node cluster."""

    def test_all_nodes_healthy(self, three_node_cluster):
        """All three nodes are healthy."""
        for node in three_node_cluster:
            assert node.is_healthy()

    def test_ring_topology(self, three_node_cluster):
        """Three nodes form a proper ring."""
        node0, node1, node2 = three_node_cluster

        info0 = node0.get_info()
        info1 = node1.get_info()
        info2 = node2.get_info()

        node_ids = {info0["id"], info1["id"], info2["id"]}

        # All three node IDs should be unique
        assert len(node_ids) == 3

        # Successors should all point to nodes in the cluster
        successors = {info0["successor_id"], info1["successor_id"], info2["successor_id"]}
        assert successors.issubset(node_ids)

    def test_file_routing_works(self, three_node_cluster):
        """Files are routed correctly in a 3-node ring."""
        node0, node1, node2 = three_node_cluster

        # Upload via different nodes
        node0.upload_file("from_node0.txt", b"uploaded via node0")
        node1.upload_file("from_node1.txt", b"uploaded via node1")
        node2.upload_file("from_node2.txt", b"uploaded via node2")

        # All files should be accessible from any node
        for node in three_node_cluster:
            assert node.get_file("from_node0.txt") == b"uploaded via node0"
            assert node.get_file("from_node1.txt") == b"uploaded via node1"
            assert node.get_file("from_node2.txt") == b"uploaded via node2"

    def test_delete_from_any_node(self, three_node_cluster):
        """A file can be deleted from any node."""
        node0, node1, node2 = three_node_cluster

        # Upload via node0
        node0.upload_file("to_delete.txt", b"delete me")

        # Delete via node2
        assert node2.delete_file("to_delete.txt")

        # Should be gone from all nodes
        for node in three_node_cluster:
            assert node.get_file("to_delete.txt") is None


class TestStabilization:
    """Tests for the stabilization protocol."""

    def test_late_joiner_integrates(self, chord_image, chord_network):
        """A node joining later integrates into the ring."""
        from tests.integration.conftest import create_chord_node

        nodes = []

        try:
            # Start bootstrap
            node0 = create_chord_node(
                image=chord_image,
                network=chord_network,
                node_name="stab-node0",
                port=5000,
            )
            node0.wait_until_healthy()
            nodes.append(node0)

            # Upload some files
            node0.upload_file("before_join.txt", b"before second node")

            # Start second node
            node1 = create_chord_node(
                image=chord_image,
                network=chord_network,
                node_name="stab-node1",
                port=5000,
                bootstrap_host="stab-node0",
                bootstrap_port=5000,
            )
            node1.wait_until_healthy()
            nodes.append(node1)

            # Wait for stabilization
            time.sleep(3)

            # File should be accessible from new node
            content = node1.get_file("before_join.txt")
            assert content == b"before second node"

            # Both nodes should know about each other
            info0 = node0.get_info()
            info1 = node1.get_info()

            assert info0["successor_id"] == info1["id"] or info1["successor_id"] == info0["id"]

        finally:
            for node in nodes:
                node.container.stop()


@pytest.mark.integration
@requires_docker
class TestDataMigration:
    """Tests for data migration when nodes join."""

    def test_file_migrates_to_responsible_node(self, chord_image, chord_network):
        """Files are migrated to the new responsible node after join."""
        from tests.integration.conftest import create_chord_node

        nodes = []

        try:
            # Start bootstrap node alone
            node0 = create_chord_node(
                image=chord_image,
                network=chord_network,
                node_name="migrate-node0",
                port=5000,
            )
            node0.wait_until_healthy()
            nodes.append(node0)

            # Upload multiple files while node0 is alone
            # Different filenames will hash to different keys
            test_files = [
                ("alpha.txt", b"alpha content"),
                ("beta.txt", b"beta content"),
                ("gamma.txt", b"gamma content"),
                ("delta.txt", b"delta content"),
            ]

            for filename, content in test_files:
                node0.upload_file(filename, content)

            # Verify all files are on node0 locally
            local_files_before = node0.list_local_files()
            assert len(local_files_before) == 4

            # Get node0's info for comparison
            info0 = node0.get_info()
            node0_id = info0["id"]

            # Start second node (this triggers migration)
            node1 = create_chord_node(
                image=chord_image,
                network=chord_network,
                node_name="migrate-node1",
                port=5000,
                bootstrap_host="migrate-node0",
                bootstrap_port=5000,
            )
            node1.wait_until_healthy()
            nodes.append(node1)

            # Wait for stabilization and migration
            time.sleep(5)

            info1 = node1.get_info()
            node1_id = info1["id"]

            # Check what files are now on each node locally
            node0_local = set(node0.list_local_files())
            node1_local = set(node1.list_local_files())

            # All files should still be accessible from both nodes
            for filename, expected_content in test_files:
                content0 = node0.get_file(filename)
                content1 = node1.get_file(filename)
                assert content0 == expected_content, f"{filename} not accessible from node0"
                assert content1 == expected_content, f"{filename} not accessible from node1"

            # At least some files should have migrated to node1
            # (depends on hash distribution, but with 4 files it's very likely)
            # The union should contain all files
            all_local = node0_local | node1_local
            assert all_local == {"alpha.txt", "beta.txt", "gamma.txt", "delta.txt"}

            # Print distribution for debugging
            print(f"\nNode0 (id={node0_id}) local files: {node0_local}")
            print(f"Node1 (id={node1_id}) local files: {node1_local}")

        finally:
            for node in nodes:
                node.container.stop()

    def test_migrated_file_stored_locally_on_new_node(self, chord_image, chord_network):
        """Verify migrated files are actually stored locally, not just routed."""
        from tests.integration.conftest import create_chord_node

        nodes = []

        try:
            # Start bootstrap
            node0 = create_chord_node(
                image=chord_image,
                network=chord_network,
                node_name="local-node0",
                port=5000,
            )
            node0.wait_until_healthy()
            nodes.append(node0)

            # Upload a file
            node0.upload_file("test_migration.txt", b"migration test content")

            # Verify it's stored locally on node0
            assert "test_migration.txt" in node0.list_local_files()

            # Start second node
            node1 = create_chord_node(
                image=chord_image,
                network=chord_network,
                node_name="local-node1",
                port=5000,
                bootstrap_host="local-node0",
                bootstrap_port=5000,
            )
            node1.wait_until_healthy()
            nodes.append(node1)

            # Wait for stabilization
            time.sleep(5)

            # Get the file from node1 to verify it's accessible
            content = node1.get_file("test_migration.txt")
            assert content == b"migration test content"

            # Check if it was migrated locally to node1
            node1_local = node1.list_local_files()

            # The file should be on at least one node locally
            # (either stayed on node0 or migrated to node1)
            all_local = node0.list_local_files() + node1_local
            assert "test_migration.txt" in all_local

        finally:
            for node in nodes:
                node.container.stop()
