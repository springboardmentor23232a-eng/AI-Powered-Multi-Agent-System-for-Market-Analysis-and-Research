"""Run:  python -m fundamental_agent.train
Cleans the data, trains the KNN, evaluates it honestly, and saves the model."""
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import (GridSearchCV, LeaveOneGroupOut, RepeatedStratifiedKFold,
                                     StratifiedKFold, cross_val_predict, cross_validate,
                                     train_test_split)
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config as C
from .features import training_table
from .preprocess import load_and_clean, report_markdown


def summary(y_true, y_pred):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }


def main():
    for d in (C.MODEL_DIR, C.REPORT_DIR, C.DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # ---- 1. clean ----
    raw, df, steps = load_and_clean()
    df.to_csv(C.CLEAN_CSV, index=False)
    (C.REPORT_DIR / "cleaning_report.md").write_text(report_markdown(steps, len(raw), len(df)), encoding="utf-8")

    # ---- 2. features + labels ----
    t = training_table(df)
    X, y, groups = t[C.FEATURES], t["label"], t["Company"]
    baseline = y.value_counts(normalize=True).max()

    # ---- 3. tune k on the TRAINING part only, then test on the untouched 20 percent ----
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=C.RANDOM_STATE)
    pipe = make_pipeline(StandardScaler(), KNeighborsClassifier())
    grid = GridSearchCV(
        pipe,
        {"kneighborsclassifier__n_neighbors": [1, 3, 5, 7, 9, 11],
         "kneighborsclassifier__weights": ["uniform", "distance"]},
        scoring="f1_macro",
        cv=StratifiedKFold(5, shuffle=True, random_state=C.RANDOM_STATE),
    ).fit(Xtr, ytr)
    k = grid.best_params_["kneighborsclassifier__n_neighbors"]
    weights = grid.best_params_["kneighborsclassifier__weights"]
    best = grid.best_estimator_

    pred = best.predict(Xte)
    holdout = summary(yte, pred)
    holdout["report"] = classification_report(yte, pred, labels=C.CLASSES, output_dict=True, zero_division=0)
    holdout["confusion_matrix"] = confusion_matrix(yte, pred, labels=C.CLASSES).tolist()
    holdout["n_train"], holdout["n_test"] = len(Xtr), len(Xte)

    # ---- 4. repeated cross-validation on all rows (years of one company can be on both sides) ----
    cv = cross_validate(
        clone(best), X, y,
        cv=RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=C.RANDOM_STATE),
        scoring=["accuracy", "precision_macro", "recall_macro", "f1_macro"],
    )
    repeated = {m: {"mean": float(cv[f"test_{m}"].mean()), "std": float(cv[f"test_{m}"].std())}
                for m in ("accuracy", "precision_macro", "recall_macro", "f1_macro")}

    # ---- 5. leave-one-company-out (the model has never seen the company it is tested on) ----
    loco_pred = cross_val_predict(clone(best), X, y, cv=LeaveOneGroupOut(), groups=groups)
    loco = summary(y, loco_pred)
    loco["confusion_matrix"] = confusion_matrix(y, loco_pred, labels=C.CLASSES).tolist()
    loco["per_company_accuracy"] = {
        c: float((loco_pred[groups == c] == y[groups == c]).mean()) for c in sorted(groups.unique())
    }

    # ---- 6. final model on all rows, plus what the agent needs for its checks ----
    final = clone(best).fit(X, y)
    scaled = final[0].transform(X)
    dist, _ = NearestNeighbors(n_neighbors=k + 1).fit(scaled).kneighbors(scaled)
    threshold = float(np.percentile(dist[:, k], C.DISTANCE_PERCENTILE))
    gate = {"percentile": C.DISTANCE_PERCENTILE, "threshold": threshold,
            "training_rows_rejected": float((dist[:, k] > threshold).mean())}
    rejected = []  # how often would the gate reject a company the model has never seen?
    for c in groups.unique():
        tr, te = (groups != c).values, (groups == c).values
        sc = StandardScaler().fit(X[tr])
        nn = NearestNeighbors(n_neighbors=k + 1).fit(sc.transform(X[tr]))
        d_tr, _ = nn.kneighbors(sc.transform(X[tr]))
        limit_c = np.percentile(d_tr[:, k], C.DISTANCE_PERCENTILE)
        d_te, _ = nn.kneighbors(sc.transform(X[te]), n_neighbors=k)
        rejected.extend((d_te[:, -1] > limit_c).tolist())
    gate["unseen_company_rows_rejected"] = float(np.mean(rejected))

    artifact = {
        "pipeline": final,
        "features": C.FEATURES,
        "classes": list(final[-1].classes_),
        "k": int(k),
        "weights": weights,
        "train_stats": {f: {"min": float(X[f].min()), "max": float(X[f].max()),
                            "mean": float(X[f].mean()), "std": float(X[f].std())} for f in C.FEATURES},
        "distance_threshold": threshold,
        "train_rows": t[["Company", "Year", "label"]].to_dict("records"),
        "info": {
            "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sklearn_version": sklearn.__version__,
            "n_rows": int(len(t)),
            "n_companies": int(groups.nunique()),
            "label_counts": y.value_counts().to_dict(),
        },
    }
    joblib.dump(artifact, C.MODEL_PATH)

    metrics = {
        "dataset": {"rows_clean": int(len(df)), "rows_used": int(len(t)), "companies": int(groups.nunique()),
                    "class_counts": y.value_counts().to_dict(), "majority_baseline_accuracy": float(baseline)},
        "chosen_hyperparameters": {"k": int(k), "weights": weights, "scaling": "StandardScaler"},
        "holdout_20_percent": holdout,
        "repeated_5x5_cv": repeated,
        "leave_one_company_out": loco,
        "distance_gate": gate,
    }
    (C.REPORT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (C.REPORT_DIR / "metrics.md").write_text(metrics_markdown(metrics), encoding="utf-8")
    print(metrics_markdown(metrics))


def pct(x):
    return f"{x * 100:.1f}%"


def metrics_markdown(m) -> str:
    h, r, l = m["holdout_20_percent"], m["repeated_5x5_cv"], m["leave_one_company_out"]
    rows = [
        "# KNN results (financial health: Weak / Moderate / Strong)", "",
        f"Rows used: {m['dataset']['rows_used']} from {m['dataset']['companies']} companies. "
        f"Class counts: {m['dataset']['class_counts']}. "
        f"Always guessing the biggest class would score {pct(m['dataset']['majority_baseline_accuracy'])}.", "",
        f"Chosen settings (tuned on the training part only): k = {m['chosen_hyperparameters']['k']}, "
        f"weights = {m['chosen_hyperparameters']['weights']}, features scaled with StandardScaler.", "",
        "| Test | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) |", "|---|---|---|---|---|",
        f"| Hold-out 20% ({h['n_test']} rows) | {pct(h['accuracy'])} | {pct(h['precision_macro'])} | {pct(h['recall_macro'])} | {pct(h['f1_macro'])} |",
        f"| Repeated 5-fold CV x5 (mean) | {pct(r['accuracy']['mean'])} | {pct(r['precision_macro']['mean'])} | {pct(r['recall_macro']['mean'])} | {pct(r['f1_macro']['mean'])} |",
        f"| Leave-one-company-out | {pct(l['accuracy'])} | {pct(l['precision_macro'])} | {pct(l['recall_macro'])} | {pct(l['f1_macro'])} |",
        "", "Hold-out per class:", "", "| Class | Precision | Recall | F1 | Rows |", "|---|---|---|---|---|",
    ]
    for c in C.CLASSES:
        d = h["report"][c]
        rows.append(f"| {c} | {pct(d['precision'])} | {pct(d['recall'])} | {pct(d['f1-score'])} | {int(d['support'])} |")
    rows += ["", f"Hold-out confusion matrix (rows = true, columns = predicted, order {C.CLASSES}): {h['confusion_matrix']}", "",
             f"Leave-one-company-out confusion matrix: {l['confusion_matrix']}", "",
             "Leave-one-company-out accuracy per company: " +
             ", ".join(f"{c} {pct(a)}" for c, a in l["per_company_accuracy"].items()), "",
             f"Distance gate (rejects input unlike the training data): limit = {m['distance_gate']['percentile']}th percentile "
             f"of training distances. It would reject {pct(m['distance_gate']['training_rows_rejected'])} of training rows "
             f"and {pct(m['distance_gate']['unseen_company_rows_rejected'])} of rows from a company the model had not seen.", ""]
    return "\n".join(rows)


if __name__ == "__main__":
    main()
