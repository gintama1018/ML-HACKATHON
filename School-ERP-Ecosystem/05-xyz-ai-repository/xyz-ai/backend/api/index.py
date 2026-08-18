"""
Vercel serverless entry point for XYZ AI FastAPI backend.
Vercel's Python runtime expects a WSGI/ASGI app exported as `app` from api/index.py.
"""
import sys
import os

# Ensure the backend src is importable
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from src.main import app  # noqa: F401 — Vercel looks for `app`
