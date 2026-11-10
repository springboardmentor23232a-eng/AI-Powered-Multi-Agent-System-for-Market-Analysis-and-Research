import math
from typing import Sequence

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def as_series(values: "pd.Series | Sequence[float]") -> pd.Series:
    if isinstance(values, pd.Series):
        return values.astype(float)
    return pd.Series(list(values), dtype=float)


def check_window(window: int) -> None:
    if not isinstance(window, int) or window < 1:
        raise ValueError(f"window must be a positive integer, got {window!r}")


def valid(*xs: float | None) -> bool:
    return all(x is not None and math.isfinite(x) for x in xs)
