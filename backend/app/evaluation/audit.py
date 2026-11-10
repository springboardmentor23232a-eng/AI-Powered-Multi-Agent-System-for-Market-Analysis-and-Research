"""Score a manually labelled citation audit: python -m app.evaluation.audit evaluation_output/citation_audit_sample.csv"""
import json
import sys
from pathlib import Path

from app.evaluation.metrics import score_audit

if __name__ == "__main__":
    print(json.dumps(score_audit(Path(sys.argv[1])), indent=2))
