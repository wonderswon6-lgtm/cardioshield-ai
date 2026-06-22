"""
data_cleaning.py — Clean the raw heart disease dataset.
"""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from data_loader import load_raw, CLEANED_PATH

PROCESSED_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "dataset", "processed")


def clean(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"[clean] Dropped {before - len(df)} duplicates -> {len(df)} rows")

    # Missing values
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())

    # Fix types
    int_cols = ["age","sex","cp","fbs","restecg","exang","slope","ca","thal","target"]
    for c in int_cols:
        if c in df.columns:
            df[c] = df[c].astype(int)
    df["oldpeak"] = df["oldpeak"].astype(float)

    if save:
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        df.to_csv(CLEANED_PATH, index=False)
        print(f"[clean] Saved -> {CLEANED_PATH}")
    return df


if __name__ == "__main__":
    clean(load_raw())
