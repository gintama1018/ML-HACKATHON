import os
import sys

# Locate backend directory in local and Vercel environments
current_dir = os.path.dirname(os.path.abspath(__file__))
possible_backend_paths = [
    os.path.abspath(os.path.join(current_dir, "..", "School-ERP-Ecosystem", "05-xyz-ai-repository", "xyz-ai", "backend")),
    os.path.abspath(os.path.join(current_dir, "School-ERP-Ecosystem", "05-xyz-ai-repository", "xyz-ai", "backend")),
    os.path.abspath(os.path.join(os.getcwd(), "School-ERP-Ecosystem", "05-xyz-ai-repository", "xyz-ai", "backend")),
]

for p in possible_backend_paths:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from src.main import app
