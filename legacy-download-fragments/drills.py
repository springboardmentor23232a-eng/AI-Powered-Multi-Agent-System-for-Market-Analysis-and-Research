"""Error-recovery drills: inject failures and check the system degrades honestly instead of inventing content."""
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.graph.workflow import Deps
from app.models import AgentResult, Claim, ResearchReport, ResearchTask, TaskStatus, User
from app.services.llm import TemplateLLM
from app.services.market_data import ProviderError
from app.services.research import execute_task


@dataclass
class DrillResult:
    name: str
    passed: bool
    detail: str


class FlakyNews:
    name = "flaky-news"

    def __init__(self, base, fail_first=0, always=False):
        self.base, self.fail_first, self.always, self.calls = base, fail_first, always, 0

    def fetch(self, query, limit=15):
        self.calls += 1
        if self.always or self.calls <= self.fail_first:
            raise ProviderError("injected news outage")
        return self.base.fetch(query, limit)


class FaultyMarket:
    name = "faulty-market"

    def __init__(self, base, down=False, dirty=False):
        self.base, self.down, self.dirty = base, down, dirty

    def get_ohlcv(self, symbol, period):
        if self.down:
            raise ProviderError("injected market outage")
        df = self.base.get_ohlcv(symbol, period).copy()
        if self.dirty:
            import pandas as pd
            df = pd.concat([df, df.iloc[[10, 20]]]).reset_index(drop=True)   # duplicate dates
            df.loc[5, "close"] = None                                          # null price
        return df

    def get_financials(self, symbol):
        if self.down:
            raise ProviderError("injected market outage")
        return self.base.get_financials(symbol)


def _env():
    d = Path(tempfile.mkdtemp())
    engine = create_engine(f"sqlite:///{d / 'drill.db'}", connect_args={"check_same_thread": False, "timeout": 30})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _run(factory, market, news, ticker, now=None):
    with factory() as db:
        u = db.scalar(select(User)) or User(email="drill@x.com", password_hash="x")
        db.add(u); db.commit()
        t = ResearchTask(user_id=u.user_id, ticker=ticker, requested_period="2y"); db.add(t); db.commit()
        tid = t.task_id
    execute_task(tid, Deps(session_factory=factory, market=market, news=news, llm=TemplateLLM(),
                           max_retries=2, backoff_seconds=0, now=now))
    with factory() as db:
        task = db.get(ResearchTask, tid)
        agents = {a.agent_name: a for a in db.scalars(select(AgentResult).where(AgentResult.task_id == tid))}
        claims = list(db.scalars(select(Claim).where(Claim.task_id == tid)))
        rep = db.scalar(select(ResearchReport).where(ResearchReport.task_id == tid))
        return task, agents, claims, rep


def run_drills(market, news, ticker: str) -> list[DrillResult]:
    out: list[DrillResult] = []

    task, agents, claims, rep = _run(_env(), market, FlakyNews(news, always=True), ticker)
    ok = (task.status == TaskStatus.partial and agents["news"].status.value == "unavailable"
          and agents["news"].attempts == 3 and not [c for c in claims if c.agent_name == "news"]
          and rep is not None and "> **Unavailable.**" in rep.report_content)
    out.append(DrillResult("News API down for the whole run", ok,
                           f"task={task.status.value}, news={agents['news'].status.value} after {agents['news'].attempts} attempts, "
                           f"news claims={sum(c.agent_name == 'news' for c in claims)}"))

    task, agents, *_ = _run(_env(), market, FlakyNews(news, fail_first=1), ticker)
    out.append(DrillResult("News API fails once, then recovers", agents["news"].status.value == "success" and agents["news"].attempts == 2,
                           f"news={agents['news'].status.value}, attempts={agents['news'].attempts}"))

    factory = _env()
    now = datetime.now(timezone.utc)
    _run(factory, market, news, ticker, now=now)                                   # populate the snapshot cache
    task, agents, claims, rep = _run(factory, FaultyMarket(market, down=True), news, ticker, now=now + timedelta(days=2))
    stale = rep is not None and "serving cached snapshot" in rep.limitations
    out.append(DrillResult("Market data down, stale snapshot available", stale and task.status != TaskStatus.failed,
                           f"task={task.status.value}, stale-cache warning in report={stale}"))

    task, agents, claims, rep = _run(_env(), FaultyMarket(market, down=True), FlakyNews(news, always=True), ticker)
    out.append(DrillResult("Total outage with no cache", task.status == TaskStatus.failed and rep is None,
                           f"task={task.status.value}, report produced={rep is not None}"))

    task, agents, claims, rep = _run(_env(), FaultyMarket(market, dirty=True), news, ticker)
    flagged = rep is not None and ("Duplicate dates" in rep.limitations and "null OHLC" in rep.limitations)
    out.append(DrillResult("Dirty price data (duplicates, null price)", flagged and agents["technical"].status.value == "success",
                           f"technical={agents['technical'].status.value}, issues reported in limitations={flagged}"))
    return out
