#!/bin/bash
#
# remove_node.sh - Remove a Chord DFS node from the ring
#
# Usage:
#   ./remove_node.sh <node-name>        Remove a specific node
#   ./remove_node.sh -a                 Remove all nodes and cleanup
#   ./remove_node.sh -h                 Show help message
#

set -e

# Configuration
NETWORK_NAME="chord-network"
CONTAINER_PREFIX="chord-node"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 [OPTIONS] [node-name]"
    echo ""
    echo "Options:"
    echo "  -a, --all      Remove all chord nodes and cleanup network"
    echo "  -f, --force    Force remove (don't prompt for confirmation)"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 chord-node-0              # Remove specific node"
    echo "  $0 -a                        # Remove all nodes"
    echo "  $0 -f chord-node-1           # Force remove without confirmation"
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

# List all chord nodes
list_nodes() {
    docker ps -a --filter "name=${CONTAINER_PREFIX}-" --format "{{.Names}}\t{{.Status}}" 2>/dev/null
}

# Remove a single node
remove_node() {
    local node_name="$1"

    if ! docker ps -a --format "{{.Names}}" | grep -q "^${node_name}$"; then
        log_error "Container '$node_name' not found"
    fi

    log_info "Stopping container: $node_name"
    docker stop "$node_name" 2>/dev/null || true

    log_info "Removing container: $node_name"
    docker rm "$node_name"

    log_info "Node '$node_name' removed successfully"
    log_warn "Ring will stabilize automatically (files on this node are lost until replication is implemented)"
}

# Remove all nodes and cleanup
remove_all() {
    local nodes
    nodes=$(docker ps -a --filter "name=${CONTAINER_PREFIX}-" --format "{{.Names}}" 2>/dev/null)

    if [ -z "$nodes" ]; then
        log_info "No chord nodes found"
    else
        log_info "Removing all chord nodes..."
        for node in $nodes; do
            log_info "  Stopping $node"
            docker stop "$node" 2>/dev/null || true
            docker rm "$node"
        done
        log_info "All nodes removed"
    fi

    # Remove network if it exists
    if docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
        log_info "Removing network: $NETWORK_NAME"
        docker network rm "$NETWORK_NAME"
    fi

    log_info "Cleanup complete"
}

# Parse arguments
REMOVE_ALL=false
FORCE=false
NODE_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            REMOVE_ALL=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            log_error "Unknown option: $1"
            ;;
        *)
            NODE_NAME="$1"
            shift
            ;;
    esac
done

# Validate arguments
if [ "$REMOVE_ALL" = false ] && [ -z "$NODE_NAME" ]; then
    echo "Current nodes:"
    list_nodes
    echo ""
    log_error "Specify a node name or use -a to remove all"
fi

# Confirmation prompt
if [ "$FORCE" = false ]; then
    if [ "$REMOVE_ALL" = true ]; then
        echo "This will remove ALL chord nodes and the network."
        echo "Current nodes:"
        list_nodes
        echo ""
        read -p "Are you sure? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Aborted"
            exit 0
        fi
    else
        read -p "Remove node '$NODE_NAME'? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Aborted"
            exit 0
        fi
    fi
fi

# Execute
if [ "$REMOVE_ALL" = true ]; then
    remove_all
else
    remove_node "$NODE_NAME"
fi
