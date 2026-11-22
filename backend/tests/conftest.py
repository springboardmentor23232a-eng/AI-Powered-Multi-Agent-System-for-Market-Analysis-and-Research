import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Tests always run against the sample dataset and a throwaway database, never yfinance.
_db = Path(tempfile.gettempdir()) / "orionnex_test.db"
_db.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_db.as_posix()}"
os.environ["DATA_SOURCE"] = "sample"
os.environ["SECRET_KEY"] = "test-secret-key-used-only-by-the-test-suite-0123456789"
