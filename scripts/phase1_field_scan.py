"""Phase 1 supporting scan: characterize financial field coverage across the 20-ticker
universe (focus: is missing operating_income systematic to banks, or a fixable label?).
Live network; writes only to the throwaway temp DB. Run from backend/.
"""
import os, sys, time, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.gettempdir(), "veritas_scan.db")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
import app.models as M  # noqa
from app.data.universe import UNIVERSE
from app.services.market_data import YahooProvider, get_financials, ProviderError

ENGINE = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False, "timeout": 30})
Base.metadata.create_all(ENGINE)
SF = sessionmaker(bind=ENGINE, expire_on_commit=False)
FIELDS = ("revenue", "operating_income", "net_income", "total_debt", "total_equity")
yf = YahooProvider()

print(f"{'ticker':12} {'yrs':>3} " + " ".join(f"{f[:9]:>9}" for f in FIELDS) + "  shares  longName")
complete = []
oi_missing = []
for t in UNIVERSE:
    with SF() as db:
        try:
            r = get_financials(db, yf, t, "NSE")
            annual = sorted(r.data.get("annual") or [], key=lambda y: -y["year"])
            latest = annual[0] if annual else {}
            prof = r.data.get("profile") or {}
            row = "".join(f"{'Y' if latest.get(f) is not None else '.':>10}" for f in FIELDS)
            shares = "Y" if prof.get("sharesOutstanding") else "NO"
            print(f"{t:12} {len(annual):>3} {row}  {shares:>6}  {(prof.get('longName') or '')[:34]}")
            if all(latest.get(f) is not None for f in FIELDS) and prof.get("sharesOutstanding"):
                complete.append(t)
            if latest.get("operating_income") is None:
                oi_missing.append(t)
        except ProviderError as e:
            print(f"{t:12} ProviderError: {str(e)[:90]}")
    time.sleep(1.0)

print("\nFIELD-COMPLETE (all 5 + shares):", len(complete), complete)
print("MISSING operating_income on latest FY:", len(oi_missing), oi_missing)
