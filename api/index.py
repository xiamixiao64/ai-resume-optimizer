"""Vercel serverless entrypoint - reuses the main Flask application."""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: E402


def handler(request):
    return app(request.environ, lambda status, headers: None)
