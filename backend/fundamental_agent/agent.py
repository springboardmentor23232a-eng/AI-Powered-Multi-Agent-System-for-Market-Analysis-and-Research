"""The Fundamental Analysis Agent: validate the input, classify with the KNN, explain."""
import math

import joblib
import numpy as np
import pandas as pd

from . import config as C
from .errors import AnalysisError, Reason
from .explain import build_explanation
from .features import (REQUIRED_RAW, RAW_LABELS, features_from_raw, health_score,
                       label_from_score)
from .yahoo_adapter import raw_from_yahoo


def _is_number(v):
    return isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)


class FundamentalAnalysisAgent:
    def __init__(self, model_path=C.MODEL_PATH):
        art = joblib.load(model_path)
        self.pipeline = art["pipeline"]
        self.features = art["features"]
        self.k = art["k"]
        self.stats = art["train_stats"]
        self.threshold = art["distance_threshold"]
        self.history = art["train_rows"]
        self.info = art["info"]

    # ---------- checks ----------
    def _check_values(self, raw):
        """Stage 1: every figure present and a real number."""
        reasons = []
        for f in REQUIRED_RAW:
            v = raw.get(f)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                reasons.append(Reason("missing_value", f, f"{RAW_LABELS[f]} is missing."))
            elif not _is_number(v):
                reasons.append(Reason("invalid_value", f, f"{RAW_LABELS[f]} must be a number but got {v!r}."))
            elif not math.isfinite(v):
                reasons.append(Reason("invalid_value", f, f"{RAW_LABELS[f]} is not a finite number."))
        return reasons

    def _check_consistency(self, r):
        """Stage 2: figures that cannot be true, or cannot be true together."""
        basic = [
            (r["revenue"] <= 0, "invalid_value", "revenue", "Revenue must be greater than zero."),
            (r["prev_revenue"] <= 0, "invalid_value", "prev_revenue",
             "Previous-year revenue must be greater than zero to compute growth."),
            (r["current_liabilities"] <= 0, "invalid_value", "current_liabilities",
             "Current liabilities must be greater than zero to compute the current ratio."),
            (r["total_assets"] <= 0, "invalid_value", "total_assets", "Total assets must be greater than zero."),
            (r["total_debt"] < 0, "invalid_value", "total_debt", "Total debt cannot be negative."),
            (r["current_assets"] < 0, "invalid_value", "current_assets", "Current assets cannot be negative."),
        ]
        reasons = [Reason(code, field, msg) for cond, code, field, msg in basic if cond]
        if reasons:  # comparing against an invalid revenue would only produce confusing extra errors
            return reasons
        relations = [
            (r["gross_profit"] > r["revenue"], "gross_profit",
             f"Gross profit ({r['gross_profit']:,.0f}) is larger than revenue ({r['revenue']:,.0f}), which is impossible."),
            (r["net_income"] > r["revenue"], "net_income",
             f"Net income ({r['net_income']:,.0f}) is larger than revenue ({r['revenue']:,.0f}), which is impossible."),
            (r["ebitda"] > r["revenue"], "ebitda",
             f"EBITDA ({r['ebitda']:,.0f}) is larger than revenue ({r['revenue']:,.0f}), which is impossible."),
        ]
        return [Reason("inconsistent_data", field, msg) for cond, field, msg in relations if cond]

    def _check_training_range(self, feats):
        """Stage 3a: any ratio outside what the model has seen."""
        reasons = []
        for name in self.features:
            lo, hi = self.stats[name]["min"], self.stats[name]["max"]
            v = feats[name]
            if v < lo or v > hi:
                reasons.append(Reason(
                    "outside_training_range", name,
                    f"{C.FEATURE_LABELS[name]} is {v:,.1f}, outside the range the model was trained on "
                    f"({lo:,.1f} to {hi:,.1f}). The model cannot judge values it has never seen."))
        return reasons

    # ---------- main entry points ----------
    def analyze(self, raw: dict, company=None, currency=None, amount_unit=1.0) -> dict:
        reasons = self._check_values(raw)
        if reasons:
            raise AnalysisError(reasons)
        reasons = self._check_consistency(raw)
        if reasons:
            raise AnalysisError(reasons)

        feats = features_from_raw(raw)
        reasons = self._check_training_range(feats)
        if reasons:
            raise AnalysisError(reasons)

        x = pd.DataFrame([feats], columns=self.features)
        scaled = self.pipeline[0].transform(x)
        knn = self.pipeline[-1]
        dist, idx = knn.kneighbors(scaled, n_neighbors=self.k)
        limit = self.threshold
        if dist[0, -1] > limit:
            raise AnalysisError([Reason(
                "unlike_training_data", None,
                "This company's combination of ratios is unlike any company-year the model was trained on "
                f"(distance to its {self.k}th closest match is {dist[0, -1]:.2f}, the limit is {limit:.2f}). "
                "The model cannot give a reliable answer.")])

        proba = self.pipeline.predict_proba(x)[0]
        classes = list(knn.classes_)
        label = classes[int(np.argmax(proba))]
        neighbours = [self.history[i] for i in idx[0]]
        score = health_score(feats)

        return {
            "status": "ok",
            "company": company,
            "classification": label,
            "confidence": float(proba.max()),
            "probabilities": {c: float(p) for c, p in zip(classes, proba)},
            "rubric_class": label_from_score(score),
            "rubric_score": score,
            "metrics": {k: round(v, 2) for k, v in feats.items()},
            "explanation": build_explanation(raw, feats, label, neighbours, self.k, currency, amount_unit),
            "nearest_matches": neighbours,
            "model_info": {"algorithm": f"KNN (k={self.k}, distance-weighted)",
                           "trained_on": f"{self.info['n_rows']} company-years from {self.info['n_companies']} companies (2009-2023)",
                           "trained_at": self.info["trained_at"]},
            "note": "Educational analysis. It reflects only the figures supplied and a small training set; it is not investment advice.",
        }

    def analyze_from_yahoo(self, fin: dict, company=None) -> dict:
        """fin = the dict returned by market_data.get_financials(ticker, 'annual')."""
        raw, reasons = raw_from_yahoo(fin)
        if reasons:
            raise AnalysisError(reasons)
        return self.analyze(raw, company=company, currency=fin.get("currency"), amount_unit=1.0)
