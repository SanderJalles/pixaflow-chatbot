import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve()))

# Mock the app module to prevent auto-initialization
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
