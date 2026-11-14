"""Entrypoint for serverless hosting.

Vercel's Python runtime looks for an ASGI app at api/index.py. The application
itself lives in app/main.py and is unchanged by this; this only re-exports it
so the platform can find it.
"""

from app.main import app

__all__ = ["app"]
