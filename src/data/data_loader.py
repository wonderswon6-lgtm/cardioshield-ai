"""
data_loader.py — Load raw and processed datasets.
"""
import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_PATH       = os.path.join(BASE_DIR, "dataset", "raw", "heart.csv")
CLEANED_PATH   = os.path.join(BASE_DIR, "dataset", "processed", "cleaned_heart.csv")
TRAIN_PATH     = os.path.join(BASE_DIR, "dataset", "processed", "train.csv")
TEST_PATH      = os.path.join(BASE_DIR, "dataset", "processed", "test.csv")

FEATURE_COLS = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"]
TARGET_COL   = "target"


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH)
    print(f"[loader] Raw: {df.shape}")
    return df

def load_cleaned() -> pd.DataFrame:
    df = pd.read_csv(CLEANED_PATH)
    print(f"[loader] Cleaned: {df.shape}")
    return df

def load_train_test():
    return pd.read_csv(TRAIN_PATH), pd.read_csv(TEST_PATH)

def xy_split(df: pd.DataFrame):
    return df[FEATURE_COLS], df[TARGET_COL]
