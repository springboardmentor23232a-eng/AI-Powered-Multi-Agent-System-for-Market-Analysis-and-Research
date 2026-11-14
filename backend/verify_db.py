import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, engine
from app import models
from sqlalchemy import text

print("Connecting and initializing database...")
init_db()

with engine.connect() as conn:
    query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    tables = [r[0] for r in conn.execute(query).fetchall()]
    print("\nVERIFIED TABLES IN multi_agent_stock_db:")
    for t in tables:
        print(f"  [OK] {t}")
        
    expected_tables = {
        "users",
        "user_auth_accounts",
        "research_tasks",
        "agent_results",
        "source_documents",
        "research_reports",
        "saved_stocks"
    }
    
    missing = expected_tables - set(tables)
    if missing:
        print(f"\n[ERROR] Missing tables: {missing}")
        sys.exit(1)
    else:
        print("\nAll 7 required tables exist and are properly configured!")

