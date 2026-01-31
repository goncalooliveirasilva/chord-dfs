"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.chord import router as chord_router
from src.api.routes.files import router as files_router
from src.config import Settings, get_settings
from src.services.node_service import NodeService

logger = logging.getLogger(__name__)


def setup_logging(settings: Settings) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle.

    Handles startup and shutdown events.
    - Startup: Initialize node, join ring, start stabilization
    - Shutdown: Stop stabilization, graceful cleanup
    """
    settings: Settings = app.state.settings

    # Build bootstrap address if provided
    bootstrap_address: tuple[str, int] | None = None
    if settings.bootstrap_host and settings.bootstrap_port:
        bootstrap_address = (settings.bootstrap_host, settings.bootstrap_port)

    # Initialize NodeService
    node_service = NodeService(
        host=settings.host,
        port=settings.port,
        bootstrap_address=bootstrap_address,
        m_bits=settings.m_bits,
        stabilize_interval=settings.stabilize_interval,
        storage_path=settings.storage_path,
    )

    # Store in app state for route access
    app.state.node_service = node_service

    # Start the service (joins ring and starts stabilization loop)
    await node_service.start()

    yield

    # Shutdown
    await node_service.stop()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings (Settings | None, optional): Application settings.
            If None, loads the environment. Defaults to None.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    if settings is None:
        settings = get_settings()

    setup_logging(settings)

    app = FastAPI(
        title="Chord DFS",
        description="Distributed File System built on Chord DHT",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Store settings in app state for access in lifespan and routes
    app.state.settings = settings

    # Register routes
    app.include_router(files_router)
    app.include_router(chord_router)

    return app
