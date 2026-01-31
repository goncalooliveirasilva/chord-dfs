"""Entry point for the Chord DFS application."""

import uvicorn

from src.api.app import create_app
from src.config import get_settings

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
    )
