"""
explanation_service.py — Perturbation-based local feature importance.
"""
import os
import pickle
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODELS_DIR = os.path.join(BASE_DIR, "saved_models")
CLEANED_PATH = os.path.join(BASE_DIR, "dataset", "processed", "cleaned_heart.csv")

FEATURE_COLS = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"]
NUMERIC_COLS = ["age","trestbps","chol","thalach","oldpeak"]

FEATURE_LABELS = {
    "age": "Age",
    "sex": "Sex",
    "cp": "Chest Pain Type",
    "trestbps": "Resting Blood Pressure",
    "chol": "Serum Cholesterol",
    "fbs": "Fasting Blood Sugar",
    "restecg": "Resting ECG Results",
    "thalach": "Max Heart Rate Achieved",
    "exang": "Exercise Induced Angina",
    "oldpeak": "ST Depression (Oldpeak)",
    "slope": "ST Slope",
    "ca": "Major Vessels Colored (ca)",
    "thal": "Thalassemia Type"
}

# Cache for models/scaler and feature baselines
_cache = {}
_baselines = {}

def _load(filename: str):
    if filename in _cache:
        return _cache[filename]
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file missing: {path}")
    with open(path, "rb") as f:
        obj = pickle.load(f)
    _cache[filename] = obj
    return obj

def get_baselines():
    global _baselines
    if _baselines:
        return _baselines
    
    # Calculate means from cleaned dataset
    if os.path.exists(CLEANED_PATH):
        try:
            df = pd.read_csv(CLEANED_PATH)
            for col in FEATURE_COLS:
                if col in df.columns:
                    _baselines[col] = float(df[col].mean())
        except Exception:
            pass
            
    # Fallbacks if loading fails
    fallbacks = {
        "age": 54.3, "sex": 0.68, "cp": 0.96, "trestbps": 131.6, "chol": 246.2,
        "fbs": 0.15, "restecg": 0.52, "thalach": 149.6, "exang": 0.33,
        "oldpeak": 1.04, "slope": 1.4, "ca": 0.73, "thal": 2.31
    }
    for col in FEATURE_COLS:
        if col not in _baselines:
            _baselines[col] = fallbacks[col]
            
    return _baselines

def format_feature_val(col: str, val: float) -> str:
    """Formats feature values for presentation with units and descriptions."""
    if col == "sex":
        return "Male" if int(val) == 1 else "Female"
    elif col == "fbs":
        return "> 120 mg/dl" if int(val) == 1 else "<= 120 mg/dl"
    elif col == "exang":
        return "Yes" if int(val) == 1 else "No"
    elif col == "cp":
        mapping = {0: "Typical Angina", 1: "Atypical Angina", 2: "Non-Anginal", 3: "Asymptomatic"}
        return mapping.get(int(val), str(int(val)))
    elif col == "restecg":
        mapping = {0: "Normal", 1: "ST-T Abnormality", 2: "LV Hypertrophy"}
        return mapping.get(int(val), str(int(val)))
    elif col == "slope":
        mapping = {0: "Upsloping", 1: "Flat", 2: "Downsloping"}
        return mapping.get(int(val), str(int(val)))
    elif col == "thal":
        mapping = {1: "Normal", 2: "Fixed Defect", 3: "Reversible Defect"}
        return mapping.get(int(val), str(int(val)))
    elif col == "age":
        return f"{int(val)} yrs"
    elif col == "trestbps":
        return f"{int(val)} mmHg"
    elif col == "chol":
        return f"{int(val)} mg/dl"
    elif col == "thalach":
        return f"{int(val)} bpm"
    elif col == "oldpeak":
        return f"{val:.1f}"
    return str(val)

def _scale(data: dict) -> pd.DataFrame:
    scaler = _load("scaler.pkl")
    df = pd.DataFrame([{c: float(data.get(c, 0)) for c in FEATURE_COLS}])
    df[NUMERIC_COLS] = scaler.transform(df[NUMERIC_COLS])
    return df

def explain_prediction(patient_data: dict, model_name: str = "random_forest") -> list:
    """
    Computes local feature contributions for a specific prediction using perturbation analysis.
    Returns a list of dicts sorted by absolute contribution magnitude descending.
    """
    name_map = {
        "logistic_regression": "logistic_regression.pkl",
        "decision_tree":       "decision_tree.pkl",
        "random_forest":       "random_forest.pkl",
        "neural_network":      "neural_network.pkl",
    }
    fname = name_map.get(model_name, "random_forest.pkl")
    try:
        model = _load(fname)
    except FileNotFoundError:
        # If models aren't trained, return empty list
        return []

    # 1. Base prediction probability
    base_X = _scale(patient_data)
    if hasattr(model, "predict_proba"):
        base_prob = float(model.predict_proba(base_X)[0][1])
    else:
        # Fallback for models without predict_proba
        base_prob = float(model.predict(base_X)[0])

    baselines = get_baselines()
    contributions = []

    # 2. Perturbation for each feature
    for col in FEATURE_COLS:
        perturbed_data = patient_data.copy()
        
        # Substitute feature value with its baseline
        perturbed_data[col] = baselines[col]
        
        # Scale and predict
        perturbed_X = _scale(perturbed_data)
        if hasattr(model, "predict_proba"):
            perturbed_prob = float(model.predict_proba(perturbed_X)[0][1])
        else:
            perturbed_prob = float(model.predict(perturbed_X)[0])
            
        # Contribution is the difference in probability (converted to percentage points)
        diff = (base_prob - perturbed_prob) * 100
        
        # Format values for frontend readability
        val_str = format_feature_val(col, float(patient_data[col]))
        base_str = format_feature_val(col, baselines[col])
        
        contributions.append({
            "feature": col,
            "label": FEATURE_LABELS.get(col, col),
            "value": val_str,
            "baseline": base_str,
            "contribution": round(diff, 2)
        })

    # 3. Sort by absolute contribution descending
    contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    return contributions
