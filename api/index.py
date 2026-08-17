import os
import sys

# Add backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "School-ERP-Ecosystem", "05-xyz-ai-repository", "xyz-ai", "backend"))

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the FastAPI application instance
from src.main import app
