"""
prediction_service.py — Load models, run predictions, categorise risk.
"""
import os, pickle
import pandas as pd

BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODELS_DIR  = os.path.join(BASE_DIR, "saved_models")
SRC_DATA    = os.path.join(BASE_DIR, "src", "data")

import sys
sys.path.insert(0, SRC_DATA)

FEATURE_COLS = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"]
NUMERIC_COLS = ["age","trestbps","chol","thalach","oldpeak"]

_cache: dict = {}

RECOMMENDATIONS = {
    "Low":      "Your risk indicators are within normal range. Maintain a heart-healthy lifestyle: regular exercise, balanced diet, no smoking, and routine check-ups.",
    "Moderate": "Moderate cardiovascular risk detected. Consult your cardiologist, monitor blood pressure and cholesterol, and adopt lifestyle changes immediately.",
    "High":     "High cardiovascular risk detected. Seek immediate medical evaluation. Do not delay consulting a specialist. Urgent lifestyle and medical intervention required.",
}


def _load(filename: str):
    if filename in _cache: return _cache[filename]
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file missing: {path}\nRun: python main.py --train")
    with open(path, "rb") as f: obj = pickle.load(f)
    _cache[filename] = obj
    return obj


def _scale(data: dict) -> pd.DataFrame:
    scaler = _load("scaler.pkl")
    df = pd.DataFrame([{c: float(data.get(c, 0)) for c in FEATURE_COLS}])
    df[NUMERIC_COLS] = scaler.transform(df[NUMERIC_COLS])
    return df


def predict(data: dict, model_name: str = "random_forest") -> dict:
    name_map = {
        "logistic_regression": "logistic_regression.pkl",
        "decision_tree":       "decision_tree.pkl",
        "random_forest":       "random_forest.pkl",
        "neural_network":      "neural_network.pkl",
    }
    fname = name_map.get(model_name, "random_forest.pkl")
    model = _load(fname)
    X     = _scale(data)

    pred = int(model.predict(X)[0])
    prob = float(model.predict_proba(X)[0][1]) if hasattr(model, "predict_proba") else float(pred)
    conf = max(prob, 1 - prob)

    if prob < 0.35:   risk = "Low"
    elif prob < 0.65: risk = "Moderate"
    else:             risk = "High"

    return {
        "prediction":     pred,
        "probability":    round(prob * 100, 2),       # percentage
        "confidence":     round(conf * 100, 2),       # percentage
        "risk_level":     risk,
        "recommendation": RECOMMENDATIONS[risk],
        "model_used":     model_name,
    }


def get_available_models() -> list:
    files = {"logistic_regression":"logistic_regression.pkl",
             "decision_tree":"decision_tree.pkl",
             "random_forest":"random_forest.pkl",
             "neural_network":"neural_network.pkl"}
    return [k for k, v in files.items() if os.path.exists(os.path.join(MODELS_DIR, v))]


def models_trained() -> bool:
    return os.path.exists(os.path.join(MODELS_DIR, "scaler.pkl"))
