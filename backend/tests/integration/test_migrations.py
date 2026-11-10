import os
import subprocess
import sys

from sqlalchemy import create_engine, inspect

EXPECTED = {"users", "research_tasks", "agent_results", "source_documents", "research_reports",
            "saved_stocks", "claims", "contradictions", "evaluation_runs"}


def test_alembic_upgrade_creates_all_tables(tmp_path):
    db = tmp_path / "m.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}"}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, env=env,
                   cwd=os.path.join(os.path.dirname(__file__), "..", ".."))
    assert EXPECTED <= set(inspect(create_engine(f"sqlite:///{db}")).get_table_names())
