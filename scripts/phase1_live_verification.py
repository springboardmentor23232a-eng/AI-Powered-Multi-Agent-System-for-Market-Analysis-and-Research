"""Phase 1 live verification harness. NOT part of the test suite; runs the real
YahooProvider + GoogleNewsRssProvider + TemplateLLM against live network data.
It writes only to a throwaway SQLite DB under the system temp dir and makes no
changes to the application code or the dev database.

Run:  cd backend && python ../scripts/phase1_live_verification.py
"""
import os
import sys
import uuid
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.gettempdir(), "veritas_live.db")

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models as M
from app.services.market_data import YahooProvider, get_prices, get_financials, ProviderError
from app.services.news import GoogleNewsRssProvider
from app.services.llm import TemplateLLM
from app.graph.workflow import Deps
from app.services.research import execute_task

ENGINE = create_engine(os.environ["DATABASE_URL"],
                       connect_args={"check_same_thread": False, "timeout": 30})
Base.metadata.create_all(ENGINE)
SF = sessionmaker(bind=ENGINE, expire_on_commit=False)

FUND_FIELDS = ("revenue", "operating_income", "net_income", "total_debt", "total_equity")
TICKERS = ["TCS", "INFY", "ITC", "HDFCBANK", "RELIANCE"]

yf = YahooProvider()


def section(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ---- 1. Yahoo financials: every field the Fundamental agent reads ----
section("1. LIVE YahooProvider.get_financials - field coverage for Fundamental agent")
fin_status = {}
for t in TICKERS:
    with SF() as db:
        try:
            r = get_financials(db, yf, t, "NSE")
            annual = sorted(r.data.get("annual") or [], key=lambda y: -y["year"])
            prof = r.data.get("profile") or {}
            latest = annual[0] if annual else {}
            present = {f: latest.get(f) is not None for f in FUND_FIELDS}
            yrs = len(annual)
            shares = prof.get("sharesOutstanding")
            fin_status[t] = (yrs, present, shares)
            print(f"{t:10} years={yrs:>2} sharesOutstanding={'yes' if shares else 'NO':>3} "
                  f"longName={prof.get('longName')!r} "
                  + " ".join(f"{f}={'Y' if present[f] else '.'}" for f in FUND_FIELDS))
            for i in r.issues:
                print(f"           issue[{i.severity}] {i.code}: {i.message}")
        except ProviderError as e:
            print(f"{t:10} ProviderError: {str(e)[:120]}")
            fin_status[t] = None

# ---- 2. Yahoo prices ----
section("2. LIVE YahooProvider.get_prices (period=2y)")
for t in TICKERS:
    with SF() as db:
        try:
            r = get_prices(db, yf, t, "NSE", "2y")
            v = r.validation
            last = r.rows[-1] if r.rows else None
            print(f"{t:10} rows {v.rows_in}->{v.rows_out} usable={v.is_usable} "
                  f"last={(last['date'] + ':' + str(last['close'])) if last else 'NA'} "
                  f"issues={[i.code for i in v.issues]}")
        except ProviderError as e:
            print(f"{t:10} ProviderError: {str(e)[:120]}")

# ---- 3. Google News RSS ----
section("3. LIVE GoogleNewsRssProvider.fetch")
news = GoogleNewsRssProvider()
try:
    arts = news.fetch("Tata Consultancy Services TCS NSE stock", limit=8)
    print(f"articles returned: {len(arts)}")
    for a in arts[:6]:
        print(f"  - [{a.published_at}] {a.title[:70]} | pub={a.publisher} | url_ok={a.url.startswith('http')}")
except ProviderError as e:
    print("news ProviderError:", str(e)[:160])

# ---- 4. Full TCS task end-to-end -> evidence.percent ----
section("4. LIVE end-to-end execute_task for TCS")
with SF() as db:
    user = M.User(user_id=uuid.uuid4(), email=f"live-{uuid.uuid4().hex[:8]}@example.com",
                  password_hash="x", preferences={})
    db.add(user)
    db.commit()
    tid = uuid.uuid4()
    db.add(M.ResearchTask(task_id=tid, user_id=user.user_id, ticker="TCS", market="NSE",
                          requested_period="2y", status=M.TaskStatus.queued))
    db.commit()

deps = Deps(session_factory=SF, market=YahooProvider(), news=GoogleNewsRssProvider(), llm=TemplateLLM())
execute_task(tid, deps)

with SF() as db:
    task = db.get(M.ResearchTask, tid)
    claims = list(db.scalars(select(M.Claim).where(M.Claim.task_id == tid)))
    report = db.scalar(select(M.ResearchReport).where(M.ResearchReport.task_id == tid))
    total = len(claims)
    verified = sum(c.verified for c in claims)
    pct = round(100 * verified / total, 1) if total else 0.0
    print(f"task.status = {task.status.value}  latency_ms={task.latency_ms}")
    print(f"claims total={total} verified={verified} blocked={total - verified} evidence.percent={pct}")
    for c in claims:
        if not c.verified:
            print(f"  BLOCKED {c.ref} ({c.claim_type.value} {c.agent_name}): {c.verification_note}")
    if report:
        print("report head:")
        for ln in report.report_content.splitlines()[:6]:
            print("   ", ln)
    for a in sorted(db.scalars(select(M.AgentResult).where(M.AgentResult.task_id == tid)),
                    key=lambda x: x.agent_name):
        print(f"  agent {a.agent_name:12} status={a.status.value} attempts={a.attempts} "
              f"latency={a.latency_ms}ms err={a.error_message}")

section("PHASE1 SUMMARY")
print("LLM used: TemplateLLM (no ANTHROPIC/LLM_API_KEY set) -> AnthropicLLM not exercised")
complete = [t for t, v in fin_status.items() if v and v[1] and all(v[1].values())]
print(f"financials field-complete tickers (all 5 Fund fields on latest FY): {complete}")
