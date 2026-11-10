"""Financial ratios. Pure functions.

Every function returns None when the result would be undefined or misleading
(missing input, zero/negative denominator, negative earnings for P/E). Callers must
report such gaps as limitations rather than substitute a number.
"""
from app.tools._common import valid


def growth_rate(current: float | None, previous: float | None) -> float | None:
    if not valid(current, previous) or previous <= 0:
        return None
    return (current - previous) / previous


def cagr(begin: float | None, end: float | None, years: float) -> float | None:
    if not valid(begin, end, years) or begin <= 0 or end <= 0 or years <= 0:
        return None
    return (end / begin) ** (1.0 / years) - 1.0


def margin(numerator: float | None, revenue: float | None) -> float | None:
    if not valid(numerator, revenue) or revenue <= 0:
        return None
    return numerator / revenue


def debt_to_equity(total_debt: float | None, total_equity: float | None) -> float | None:
    if not valid(total_debt, total_equity) or total_equity <= 0:
        return None
    return total_debt / total_equity


def roe(net_income: float | None, equity_end: float | None, equity_begin: float | None = None) -> float | None:
    """Return on equity. Uses average equity when `equity_begin` is given."""
    if equity_begin is not None:
        if not valid(net_income, equity_end, equity_begin):
            return None
        base = (equity_end + equity_begin) / 2.0
    else:
        if not valid(net_income, equity_end):
            return None
        base = equity_end
    return net_income / base if base > 0 else None


def eps(net_income: float | None, shares: float | None) -> float | None:
    if not valid(net_income, shares) or shares <= 0:
        return None
    return net_income / shares


def book_value_per_share(total_equity: float | None, shares: float | None) -> float | None:
    if not valid(total_equity, shares) or shares <= 0:
        return None
    return total_equity / shares


def pe_ratio(price: float | None, earnings_per_share: float | None) -> float | None:
    if not valid(price, earnings_per_share) or earnings_per_share <= 0:
        return None
    return price / earnings_per_share


def pb_ratio(price: float | None, book_value_ps: float | None) -> float | None:
    if not valid(price, book_value_ps) or book_value_ps <= 0:
        return None
    return price / book_value_ps
