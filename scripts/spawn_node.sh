#!/bin/bash
#
# spawn_node.sh - Create and start a Chord DFS node
#
# Usage:
#   ./spawn_node.sh -b                  Start the first node (creates network)
#   ./spawn_node.sh -j <host:port>      Join an existing ring
#   ./spawn_node.sh -h                  Show help message
#

set -e

# Configuration
IMAGE_NAME="chord-dfs"
NETWORK_NAME="chord-network"
CONTAINER_PREFIX="chord-node"
INTERNAL_PORT=5000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --bootstrap          Start the first node (creates the ring)"
    echo "  -j, --join <host:port>   Join an existing ring via bootstrap node"
    echo "  -n, --name <name>        Custom node name (default: auto-generated)"
    echo "  -p, --port <port>        Host port to expose (default: auto-assigned)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -b                              # Start first node"
    echo "  $0 -j chord-node-0:5000            # Join via node-0"
    echo "  $0 -j chord-node-0:5000 -n mynode -p 5001"
    exit 0
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Get the next available node number
get_next_node_number() {
    local max_num=-1
    for container in $(docker ps -a --filter "name=${CONTAINER_PREFIX}-" --format "{{.Names}}" 2>/dev/null); do
        num="${container##${CONTAINER_PREFIX}-}"
        if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -gt "$max_num" ]; then
            max_num="$num"
        fi
    done
    echo $((max_num + 1))
}

# Get the next available host port
get_next_port() {
    local base_port=5000
    local port=$base_port
    while docker ps --format "{{.Ports}}" | grep -q "0.0.0.0:${port}->"; do
        ((port++))
    done
    echo "$port"
}

# Ensure the Docker network exists
ensure_network() {
    if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
        log_info "Creating Docker network: $NETWORK_NAME"
        docker network create "$NETWORK_NAME"
    fi
}

# Ensure the Docker image exists
ensure_image() {
    if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
        log_info "Building Docker image: $IMAGE_NAME"
        docker build -t "$IMAGE_NAME" "$(dirname "$0")/.."
    fi
}

# Parse arguments
BOOTSTRAP=false
JOIN_ADDRESS=""
NODE_NAME=""
HOST_PORT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--bootstrap)
            BOOTSTRAP=true
            shift
            ;;
        -j|--join)
            JOIN_ADDRESS="$2"
            shift 2
            ;;
        -n|--name)
            NODE_NAME="$2"
            shift 2
            ;;
        -p|--port)
            HOST_PORT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            ;;
    esac
done

# Validate arguments
if [ "$BOOTSTRAP" = false ] && [ -z "$JOIN_ADDRESS" ]; then
    log_error "Must specify either --bootstrap or --join <host:port>"
fi

if [ "$BOOTSTRAP" = true ] && [ -n "$JOIN_ADDRESS" ]; then
    log_error "Cannot use both --bootstrap and --join"
fi

# Ensure prerequisites
ensure_network
ensure_image

# Determine node name
if [ -z "$NODE_NAME" ]; then
    NODE_NUM=$(get_next_node_number)
    NODE_NAME="${CONTAINER_PREFIX}-${NODE_NUM}"
fi

# Check if container already exists
if docker ps -a --format "{{.Names}}" | grep -q "^${NODE_NAME}$"; then
    log_error "Container '$NODE_NAME' already exists. Remove it first or choose a different name."
fi

# Determine host port
if [ -z "$HOST_PORT" ]; then
    HOST_PORT=$(get_next_port)
fi

# Build environment variables
ENV_VARS="-e CHORD_HOST=$NODE_NAME -e CHORD_PORT=$INTERNAL_PORT"

if [ -n "$JOIN_ADDRESS" ]; then
    # Parse host:port
    BOOTSTRAP_HOST="${JOIN_ADDRESS%:*}"
    BOOTSTRAP_PORT="${JOIN_ADDRESS#*:}"

    # Validate port is a number
    if ! [[ "$BOOTSTRAP_PORT" =~ ^[0-9]+$ ]]; then
        log_error "Invalid bootstrap address format. Use host:port (e.g., chord-node-0:5000)"
    fi

    ENV_VARS="$ENV_VARS -e CHORD_BOOTSTRAP_HOST=$BOOTSTRAP_HOST -e CHORD_BOOTSTRAP_PORT=$BOOTSTRAP_PORT"
fi

# Start the container
log_info "Starting node: $NODE_NAME"
log_info "  Host port: $HOST_PORT -> Container port: $INTERNAL_PORT"
if [ -n "$JOIN_ADDRESS" ]; then
    log_info "  Joining ring via: $JOIN_ADDRESS"
else
    log_info "  Starting as bootstrap node (new ring)"
fi

CONTAINER_ID=$(docker run -d \
    --name "$NODE_NAME" \
    --network "$NETWORK_NAME" \
    -p "${HOST_PORT}:${INTERNAL_PORT}" \
    $ENV_VARS \
    "$IMAGE_NAME")

log_info "Container started: ${CONTAINER_ID:0:12}"
log_info ""
log_info "Node is accessible at:"
log_info "  - From host:       http://localhost:$HOST_PORT"
log_info "  - From containers: http://$NODE_NAME:$INTERNAL_PORT"
log_info ""
log_info "Useful commands:"
log_info "  docker logs -f $NODE_NAME     # View logs"
log_info "  curl localhost:$HOST_PORT/health   # Health check"
log_info "  curl localhost:$HOST_PORT/chord/info   # Node info"
