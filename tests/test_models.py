"""
test_models.py — Unit tests for ML models.
Run: pytest tests/
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_data():
    """Load cleaned data if available, otherwise synthesize."""
    cleaned = os.path.join(os.path.dirname(__file__), "..", "dataset", "processed", "cleaned_heart.csv")
    if os.path.exists(cleaned):
        return pd.read_csv(cleaned)
    # Synthetic fallback
    np.random.seed(42)
    n = 50
    return pd.DataFrame({
        "age": np.random.randint(30, 80, n),
        "sex": np.random.randint(0, 2, n),
        "cp":  np.random.randint(0, 4, n),
        "trestbps": np.random.randint(90, 200, n).astype(float),
        "chol":     np.random.randint(150, 400, n).astype(float),
        "fbs":  np.random.randint(0, 2, n),
        "restecg": np.random.randint(0, 3, n),
        "thalach": np.random.randint(80, 200, n).astype(float),
        "exang": np.random.randint(0, 2, n),
        "oldpeak": np.random.uniform(0, 5, n),
        "slope": np.random.randint(0, 3, n),
        "ca": np.random.randint(0, 5, n),
        "thal": np.random.randint(1, 4, n),
        "target": np.random.randint(0, 2, n),
    })


def test_data_shape(sample_data):
    assert sample_data.shape[1] == 14
    assert len(sample_data) > 0


def test_no_null_values(sample_data):
    assert sample_data.isnull().sum().sum() == 0


def test_target_binary(sample_data):
    assert set(sample_data["target"].unique()).issubset({0, 1})


def test_preprocessing_split(sample_data):
    from src.data.preprocessing import split_and_scale
    X_tr, X_te, y_tr, y_te, scaler = split_and_scale(sample_data)
    assert len(X_tr) > 0
    assert len(X_te) > 0
    assert len(X_tr) + len(X_te) == len(sample_data)


def test_models_saved():
    models_dir = os.path.join(os.path.dirname(__file__), "..", "saved_models")
    if not os.path.exists(models_dir):
        pytest.skip("Models not trained yet")
    assert os.path.exists(os.path.join(models_dir, "scaler.pkl"))


def test_prediction_service():
    from app.backend.services.prediction_service import models_trained
    if not models_trained():
        pytest.skip("Models not trained yet")
    from app.backend.services.prediction_service import predict
    patient = dict(age=63,sex=1,cp=3,trestbps=145,chol=233,fbs=1,
                   restecg=0,thalach=150,exang=0,oldpeak=2.3,slope=0,ca=0,thal=1)
    result = predict(patient, "random_forest")
    assert "prediction" in result
    assert result["prediction"] in (0, 1)
    assert 0 <= result["probability"] <= 100
    assert result["risk_level"] in ("Low", "Moderate", "High")


def test_explanation_service():
    from app.backend.services.prediction_service import models_trained
    if not models_trained():
        pytest.skip("Models not trained yet")
    from app.backend.services.explanation_service import explain_prediction
    patient = dict(age=63,sex=1,cp=3,trestbps=145,chol=233,fbs=1,
                   restecg=0,thalach=150,exang=0,oldpeak=2.3,slope=0,ca=0,thal=1)
    
    expl = explain_prediction(patient, "random_forest")
    assert isinstance(expl, list)
    assert len(expl) == 13
    
    first = expl[0]
    assert "feature" in first
    assert "label" in first
    assert "value" in first
    assert "baseline" in first
    assert "contribution" in first
    assert isinstance(first["contribution"], float)
    
    for i in range(len(expl) - 1):
        assert abs(expl[i]["contribution"]) >= abs(expl[i+1]["contribution"])

