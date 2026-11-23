import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Use SQLite for testing so tests can run stand-alone
os.environ["DATABASE_URL"] = "sqlite:///./test_stock_research.sqlite"
