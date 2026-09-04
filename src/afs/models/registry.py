"""Model construction.

Two models, held constant across every feature set. Ablating features and
classifiers at the same time confounds the whole study, so the model config is
frozen once and reused.

The linear SVM is Drebin's original classifier and is what makes closed-form
evasion cost tractable. LightGBM is the modern strong baseline; its evasion
cost is estimated by greedy search instead.
"""
from __future__ import annotations

from typing import Any

import numpy as np


def build_model(spec: dict[str, Any]):
    kind = spec["kind"]
    params = dict(spec.get("params", {}))
    if kind == "linear_svm":
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.svm import LinearSVC
        base = LinearSVC(**params)
        if spec.get("calibrate", True):
            # Needed for meaningful scores at low FPR; keeps the linear
            # decision function accessible via base_estimator for the attack.
            return CalibratedClassifierCV(base, method="sigmoid", cv=3)
        return base
    if kind == "lightgbm":
        import lightgbm as lgb
        return lgb.LGBMClassifier(**params)
    if kind == "logreg":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(**params)
    raise KeyError(f"unknown model kind {kind!r}")


MODELS = ("linear_svm", "lightgbm", "logreg")


def decision_scores(model, X: np.ndarray) -> np.ndarray:
    """Uniform score accessor: higher = more malicious."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        return model.decision_function(X)
    raise TypeError(f"{type(model).__name__} exposes no score")


def linear_weights(model) -> tuple[np.ndarray, float]:
    """Extract (w, b) from a linear model, unwrapping calibration if present."""
    est = model
    if hasattr(est, "calibrated_classifiers_"):
        inner = est.calibrated_classifiers_[0]
        est = getattr(inner, "estimator", None) or inner.base_estimator
    if not hasattr(est, "coef_"):
        raise TypeError("not a linear model; use greedy evasion instead")
    return np.ravel(est.coef_), float(np.ravel(est.intercept_)[0])
