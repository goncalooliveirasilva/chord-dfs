"""Fixtures for integration tests using testcontainers."""

import time
from pathlib import Path

import httpx
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.image import DockerImage
from testcontainers.core.network import Network


# Check if Docker is available
def is_docker_available() -> bool:
    """Check if Docker daemon is accessible."""
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


DOCKER_AVAILABLE = is_docker_available()

# Decorator to skip tests when Docker is unavailable
requires_docker = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker is not available (check permissions or if Docker is running)",
)


@pytest.fixture(scope="session")
def chord_image():
    """Build the chord-dfs Docker image."""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker is not available")
    project_root = Path(__file__).parent.parent.parent
    with DockerImage(path=str(project_root), tag="chord-dfs-test:latest") as image:
        yield image


@pytest.fixture(scope="session")
def chord_network():
    """Create a Docker network for the chord cluster."""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker is not available")
    with Network() as network:
        yield network


class ChordNode:
    """Wrapper for a chord node container."""

    def __init__(
        self,
        container: DockerContainer,
        host: str,
        port: int,
        internal_host: str,
    ):
        self.container = container
        self.host = host
        self.port = port
        self.internal_host = internal_host
        self.base_url = f"http://{host}:{port}"

    def get_info(self) -> dict:
        """Get node info from the API."""
        response = httpx.get(f"{self.base_url}/chord/info", timeout=10.0)
        response.raise_for_status()
        return response.json()

    def upload_file(self, filename: str, content: bytes) -> dict:
        """Upload a file to this node."""
        response = httpx.post(
            f"{self.base_url}/files",
            files={"file": (filename, content)},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    def get_file(self, filename: str) -> bytes | None:
        """Get a file from this node."""
        response = httpx.get(f"{self.base_url}/files/{filename}", timeout=10.0)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.content

    def list_files(self) -> list[str]:
        """List files on this node."""
        response = httpx.get(f"{self.base_url}/files", timeout=10.0)
        response.raise_for_status()
        return response.json()["files"]

    def list_local_files(self) -> list[str]:
        """List files stored locally on this node (not routed)."""
        response = httpx.get(f"{self.base_url}/files/list/local", timeout=10.0)
        response.raise_for_status()
        return response.json()["files"]

    def delete_file(self, filename: str) -> bool:
        """Delete a file from this node."""
        response = httpx.delete(f"{self.base_url}/files/{filename}", timeout=10.0)
        return response.status_code == 200

    def is_healthy(self) -> bool:
        """Check if the node is healthy."""
        try:
            response = httpx.post(f"{self.base_url}/chord/keepalive", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def wait_until_healthy(self, timeout: float = 30.0) -> None:
        """Wait until the node is healthy."""
        start = time.time()
        while time.time() - start < timeout:
            if self.is_healthy():
                return
            time.sleep(0.5)
        raise TimeoutError(f"Node {self.internal_host} did not become healthy")


def create_chord_node(
    image: DockerImage,
    network: Network,
    node_name: str,
    port: int,
    bootstrap_host: str | None = None,
    bootstrap_port: int | None = None,
) -> ChordNode:
    """Create a chord node container."""
    container = (
        DockerContainer(str(image))
        .with_name(node_name)
        .with_network(network)
        .with_network_aliases(node_name)
        .with_exposed_ports(5000)
        .with_env("CHORD_HOST", node_name)
        .with_env("CHORD_PORT", "5000")
        .with_env("CHORD_STORAGE_PATH", "/app/storage")
        .with_env("CHORD_STABILIZE_INTERVAL", "1.0")
    )

    if bootstrap_host and bootstrap_port:
        container = container.with_env("CHORD_BOOTSTRAP_HOST", bootstrap_host)
        container = container.with_env("CHORD_BOOTSTRAP_PORT", str(bootstrap_port))

    container.start()

    # Get the mapped port
    mapped_port = container.get_exposed_port(5000)
    host = container.get_container_host_ip()

    node = ChordNode(
        container=container,
        host=host,
        port=int(mapped_port),
        internal_host=node_name,
    )

    return node


@pytest.fixture
def bootstrap_node(chord_image, chord_network):
    """Create a bootstrap node (first node in the ring)."""
    node = create_chord_node(
        image=chord_image,
        network=chord_network,
        node_name="node0",
        port=5000,
    )
    node.wait_until_healthy()
    yield node
    node.container.stop()


@pytest.fixture
def two_node_cluster(chord_image, chord_network):
    """Create a 2-node cluster."""
    nodes = []

    # Bootstrap node
    node0 = create_chord_node(
        image=chord_image,
        network=chord_network,
        node_name="cluster2-node0",
        port=5000,
    )
    node0.wait_until_healthy()
    nodes.append(node0)

    # Second node joins through bootstrap
    node1 = create_chord_node(
        image=chord_image,
        network=chord_network,
        node_name="cluster2-node1",
        port=5000,
        bootstrap_host="cluster2-node0",
        bootstrap_port=5000,
    )
    node1.wait_until_healthy()
    nodes.append(node1)

    # Wait for stabilization
    time.sleep(3)

    yield nodes

    for node in nodes:
        node.container.stop()


@pytest.fixture
def three_node_cluster(chord_image, chord_network):
    """Create a 3-node cluster."""
    nodes = []

    # Bootstrap node
    node0 = create_chord_node(
        image=chord_image,
        network=chord_network,
        node_name="cluster3-node0",
        port=5000,
    )
    node0.wait_until_healthy()
    nodes.append(node0)

    # Second node
    node1 = create_chord_node(
        image=chord_image,
        network=chord_network,
        node_name="cluster3-node1",
        port=5000,
        bootstrap_host="cluster3-node0",
        bootstrap_port=5000,
    )
    node1.wait_until_healthy()
    nodes.append(node1)

    # Third node
    node2 = create_chord_node(
        image=chord_image,
        network=chord_network,
        node_name="cluster3-node2",
        port=5000,
        bootstrap_host="cluster3-node0",
        bootstrap_port=5000,
    )
    node2.wait_until_healthy()
    nodes.append(node2)

    # Wait for stabilization
    time.sleep(5)

    yield nodes

    for node in nodes:
        node.container.stop()
