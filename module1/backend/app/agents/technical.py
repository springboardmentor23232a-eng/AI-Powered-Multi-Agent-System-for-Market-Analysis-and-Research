"""Technical Analysis Agent (Milestone 2): trend, SMA/EMA/RSI/MACD, historical volatility, predefined conditions + chart series.

Indicators are computed on >= 1 year of history (warm-up) and reported for the selected window. They describe PAST price
behaviour only and are not predictions.
"""
from datetime import datetime, timezone

from ..analysis import indicators as ind
from ..analysis.technical_rules import detect_conditions, overall_bias
from .context import ResearchContext
from .schemas import ChartSeries, Condition, Finding, SourceRef, TechnicalOutput

MIN_BARS = 30


def _r(x, nd=4):
    return None if x is None else round(x, nd)


def run(ctx: ResearchContext) -> TechnicalOutput:
    stock, bars, window = ctx.stock, ctx.bars, ctx.window
    base = dict(ticker=stock.ticker, market=stock.market, generated_at=datetime.now(timezone.utc), currency=ctx.currency,
                sources=[SourceRef(name=ctx.ohlcv.source, url=ctx.ohlcv.source_url, retrieved_at=ctx.ohlcv.retrieved_at,
                                   synthetic=ctx.price_is_synthetic)])
    limitations = ["Technical indicators describe historical price behaviour and are not guaranteed predictions."]
    if ctx.price_is_synthetic:
        limitations.append("Prices are SYNTHETIC demo data, so these indicators carry no information about the real stock.")
    if len(bars) < MIN_BARS:
        return TechnicalOutput(status="Unavailable", bias="insufficient_data",
                               summary=f"Only {len(bars)} valid price rows - at least {MIN_BARS} are needed for technical analysis.",
                               limitations=limitations, **base)

    closes = [b.close for b in bars]
    n = len(window)
    s20, s50, s200 = ind.sma(closes, 20), ind.sma(closes, 50), ind.sma(closes, 200)
    e12, e26 = ind.ema(closes, 12), ind.ema(closes, 26)
    rsi14 = ind.rsi(closes, 14)
    macd_line, signal, hist = ind.macd(closes)
    wc = [b.close for b in window]
    vol = ind.annualised_volatility(wc) if len(wc) >= 20 else ind.annualised_volatility(closes)
    conditions = detect_conditions(closes)
    bias = overall_bias(conditions)
    ret = (wc[-1] / wc[0] - 1) if len(wc) > 1 and wc[0] else None

    indicators = {k: _r(v) for k, v in {
        "last_close": closes[-1], "sma_20": ind.last(s20), "sma_50": ind.last(s50), "sma_200": ind.last(s200),
        "ema_12": ind.last(e12), "ema_26": ind.last(e26), "rsi_14": ind.last(rsi14), "macd": ind.last(macd_line),
        "macd_signal": ind.last(signal), "macd_histogram": ind.last(hist),
        "annualised_volatility_pct": None if vol is None else vol * 100, "period_return_pct": None if ret is None else ret * 100,
        "period_high": max(wc) if wc else None, "period_low": min(wc) if wc else None}.items()}
    missing = [k for k in ("sma_50", "sma_200", "rsi_14", "macd") if indicators.get(k) is None]
    if missing:
        limitations.append("Not enough price history yet for: " + ", ".join(missing) + ". Choose a longer analysis period.")
    if len(window) < 20:
        limitations.append(f"The selected period has only {len(window)} trading days; volatility uses the longer warm-up history.")

    tail = slice(len(bars) - n, None) if n else slice(0, None)
    chart = ChartSeries(
        dates=[b.date.isoformat() for b in bars[tail]], open=[b.open for b in bars[tail]], high=[b.high for b in bars[tail]],
        low=[b.low for b in bars[tail]], close=[b.close for b in bars[tail]],
        **{name: [_r(v) for v in series[tail]] for name, series in (
            ("sma20", s20), ("sma50", s50), ("ema12", e12), ("ema26", e26), ("rsi14", rsi14),
            ("macd", macd_line), ("macd_signal", signal), ("macd_hist", hist))})

    findings = []
    if ret is not None:
        findings.append(Finding(text=f"Close moved {ret * 100:+.2f}% over the selected period ({window[0].date} to {window[-1].date}).",
                                kind="calculated", tone="positive" if ret > 0 else "negative"))
    for c in conditions:
        findings.append(Finding(text=c["text"], kind="interpretation",
                                tone={"bullish": "positive", "bearish": "negative", "neutral": "neutral"}[c["bias"]]))
    if vol is not None:
        findings.append(Finding(text=f"Annualised historical volatility is {vol * 100:.1f}%.", kind="calculated"))
    label = {"upward": "an upward trend", "downward": "a downward trend", "mixed": "mixed signals",
             "insufficient_data": "too little data"}[bias]
    nb = sum(c["bias"] == "bullish" for c in conditions)
    ns = sum(c["bias"] == "bearish" for c in conditions)
    summary = (f"Selected technical indicators show {label} ({nb} bullish vs {ns} bearish conditions)"
               + (f"; RSI(14) {indicators['rsi_14']:.0f}" if indicators.get("rsi_14") is not None else "") + ". Historical, not a prediction.")
    return TechnicalOutput(summary=summary, findings=findings, limitations=limitations, bias=bias, indicators=indicators,
                           conditions=[Condition(**c) for c in conditions], chart=chart, **base)
