"""Dev helper: wipe ALL tables and recreate them from the current models.

Use it when the database was created by an older version of the project (e.g. error
'column "user_id" of relation "source_documents" does not exist'): the app only creates MISSING tables,
it never alters existing ones.   Run:  python -m app.tools.reset_db --yes
WARNING: deletes every user, watchlist item and research report in the configured DATABASE_URL.
"""
import sys

from sqlalchemy import text

from ..database import Base, engine
from .. import models  # noqa: F401  (registers all tables)


def main(argv: list[str]) -> int:
    if "--yes" not in argv:
        print(f"This DELETES all data in {engine.url.render_as_string(hide_password=True)}\nRe-run with --yes to confirm.")
        return 1
    if engine.dialect.name == "postgresql":
        with engine.begin() as c:
            c.execute(text("DROP SCHEMA public CASCADE"))
            c.execute(text("CREATE SCHEMA public"))
    else:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database reset: all tables recreated with the current schema. Register a new account.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
