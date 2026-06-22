"""
preprocessing.py — Split, scale, encode and save processed datasets.
"""
import os, sys, pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
from data_loader import FEATURE_COLS, TARGET_COL, TRAIN_PATH, TEST_PATH

BASE_DIR       = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR  = os.path.join(BASE_DIR, "dataset", "processed")
MODELS_DIR     = os.path.join(BASE_DIR, "saved_models")
SCALER_PATH    = os.path.join(MODELS_DIR, "scaler.pkl")

NUMERIC_COLS   = ["age","trestbps","chol","thalach","oldpeak"]


def split_and_scale(df: pd.DataFrame, test_size=0.2, random_state=42):
    X, y = df[FEATURE_COLS], df[TARGET_COL]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=test_size,
                                               stratify=y, random_state=random_state)
    scaler = StandardScaler()
    X_tr = X_tr.copy(); X_te = X_te.copy()
    X_tr[NUMERIC_COLS] = scaler.fit_transform(X_tr[NUMERIC_COLS])
    X_te[NUMERIC_COLS]  = scaler.transform(X_te[NUMERIC_COLS])

    os.makedirs(MODELS_DIR,    exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    with open(SCALER_PATH, "wb") as f: pickle.dump(scaler, f)

    train_df = X_tr.copy(); train_df[TARGET_COL] = y_tr.values
    test_df  = X_te.copy(); test_df[TARGET_COL]  = y_te.values
    train_df.to_csv(TRAIN_PATH, index=False)
    test_df.to_csv(TEST_PATH,   index=False)
    print(f"[preprocess] Train {X_tr.shape}, Test {X_te.shape}. Scaler saved.")
    return X_tr, X_te, y_tr, y_te, scaler


def load_scaler():
    with open(SCALER_PATH, "rb") as f: return pickle.load(f)


def scale_input(data: dict) -> pd.DataFrame:
    scaler = load_scaler()
    df = pd.DataFrame([{c: float(data.get(c, 0)) for c in FEATURE_COLS}])
    df[NUMERIC_COLS] = scaler.transform(df[NUMERIC_COLS])
    return df
