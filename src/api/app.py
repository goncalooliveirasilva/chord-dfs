"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import Settings, get_settings

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

    logger.info("Starting node at %s:%s", settings.host, settings.port)

    # TODO: Initialize NodeService and start stabilization loop

    yield

    # Shutdown
    logger.info("Shutting down node")
    # TODO: Stop stabilization loop and cleanup


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

    # TODO: Register routes

    return app
