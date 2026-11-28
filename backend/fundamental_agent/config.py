"""Settings shared by training and the agent."""
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
DATA_DIR = PKG_DIR / "data"
MODEL_DIR = PKG_DIR / "model"
REPORT_DIR = PKG_DIR / "reports"

RAW_CSV = DATA_DIR / "Financial_Statements.csv"
CLEAN_CSV = DATA_DIR / "financial_statements_clean.csv"
MODEL_PATH = MODEL_DIR / "fundamental_knn.joblib"

RANDOM_STATE = 42

# Scale-free features (ratios), so the model works for any company size or currency.
FEATURES = [
    "gross_margin",
    "net_margin",
    "ebitda_margin",
    "ocf_margin",
    "current_ratio",
    "debt_equity",
    "roa",
    "rev_growth",
]

FEATURE_LABELS = {
    "gross_margin": "Gross margin (%)",
    "net_margin": "Net profit margin (%)",
    "ebitda_margin": "EBITDA margin (%)",
    "ocf_margin": "Operating cash flow margin (%)",
    "current_ratio": "Current ratio",
    "debt_equity": "Debt-to-equity ratio",
    "roa": "Return on assets (%)",
    "rev_growth": "Revenue growth (%)",
}

CLASSES = ["Weak", "Moderate", "Strong"]

# Debt-to-equity is meaningless when equity is zero or negative, so it is capped.
DEBT_EQUITY_CAP = 10.0

# ---- Financial-health rubric (creates the labels the KNN learns) ----
STRONG_NET_MARGIN = 10.0   # % -> 2 points ; 0 to 10 % -> 1 point ; below 0 -> 0 points
MIN_ROA = 5.0              # % -> 1 point
MIN_OCF_MARGIN = 10.0      # % -> 1 point
MIN_CURRENT_RATIO = 1.0    #   -> 1 point
# revenue growth above 0 -> 1 point.   Max score = 6
STRONG_AT = 5              # score >= 5 -> Strong
MODERATE_AT = 3            # score 3-4 -> Moderate ; score <= 2 -> Weak

# New input is rejected if its distance to its k-th closest training match is larger than this
# percentile of the same distance measured inside the training data.
DISTANCE_PERCENTILE = 99
