"""
train_models.py
---------------
Trains all four classifiers, tunes them, evaluates them, and saves
.pkl files to saved_models/.
Run this ONCE before starting the Flask server.
"""
import os, sys, pickle, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model   import LogisticRegression
from sklearn.tree           import DecisionTreeClassifier
from sklearn.ensemble       import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.metrics        import (accuracy_score, precision_score, recall_score,
                                    f1_score, roc_auc_score, confusion_matrix,
                                    classification_report, roc_curve)
warnings.filterwarnings("ignore")

BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR   = os.path.join(BASE_DIR, "saved_models")
REPORTS_DIR  = os.path.join(BASE_DIR, "reports")

sys.path.insert(0, os.path.join(BASE_DIR, "src", "data"))
from data_loader   import load_raw, FEATURE_COLS, TARGET_COL
from data_cleaning import clean
from preprocessing import split_and_scale


os.makedirs(MODELS_DIR,  exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)


# ── helpers ──────────────────────────────────────────────────────────────────

def evaluate(name, model, X_te, y_te) -> dict:
    yp   = model.predict(X_te)
    yprob = model.predict_proba(X_te)[:, 1] if hasattr(model, "predict_proba") else yp
    cm   = confusion_matrix(y_te, yp)
    tn, fp, fn, tp = cm.ravel()
    return dict(
        model       = name,
        accuracy    = round(accuracy_score(y_te, yp),      4),
        precision   = round(precision_score(y_te, yp, zero_division=0), 4),
        recall      = round(recall_score(y_te, yp, zero_division=0),    4),
        f1_score    = round(f1_score(y_te, yp, zero_division=0),        4),
        roc_auc     = round(roc_auc_score(y_te, yprob),    4),
        specificity = round(tn / (tn + fp) if (tn+fp) else 0, 4),
        y_pred      = yp,
        y_prob      = yprob,
        cm          = cm,
    )


def save_model(name, model):
    path = os.path.join(MODELS_DIR, f"{name}.pkl")
    with open(path, "wb") as f: pickle.dump(model, f)
    print(f"  Saved → {path}")


# ── plot helpers ─────────────────────────────────────────────────────────────

def plot_confusion_matrices(results, y_te):
    fig, axes = plt.subplots(1, len(results), figsize=(5*len(results), 4))
    if len(results) == 1: axes = [axes]
    for ax, r in zip(axes, results):
        cm = r["cm"]
        im = ax.imshow(cm, cmap="Blues")
        ax.set_title(r["model"], fontsize=11, fontweight="bold")
        ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
        ax.set_xticks([0,1]); ax.set_yticks([0,1])
        ax.set_xticklabels(["No Disease","Disease"])
        ax.set_yticklabels(["No Disease","Disease"])
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i,j]), ha="center", va="center",
                        color="white" if cm[i,j] > cm.max()/2 else "black", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, "confusion_matrices.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("[plots] confusion_matrices.png saved")


def plot_roc_curves(results, y_te):
    plt.figure(figsize=(8, 6))
    colors = ["#e74c3c","#3498db","#2ecc71","#9b59b6"]
    for r, c in zip(results, colors):
        fpr, tpr, _ = roc_curve(y_te, r["y_prob"])
        plt.plot(fpr, tpr, color=c, lw=2, label=f"{r['model']} (AUC={r['roc_auc']:.3f})")
    plt.plot([0,1],[0,1],"k--", lw=1)
    plt.xlabel("False Positive Rate"); plt.ylabel("True Positive Rate")
    plt.title("ROC Curves — Model Comparison", fontweight="bold")
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, "roc_curves.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("[plots] roc_curves.png saved")


def plot_metrics_comparison(results):
    metrics = ["accuracy","precision","recall","f1_score","roc_auc"]
    names   = [r["model"] for r in results]
    x       = np.arange(len(metrics))
    width   = 0.2
    fig, ax = plt.subplots(figsize=(12, 5))
    colors  = ["#e74c3c","#3498db","#2ecc71","#9b59b6"]
    for i, (r, c) in enumerate(zip(results, colors)):
        vals = [r[m] for m in metrics]
        bars = ax.bar(x + i*width - 1.5*width, vals, width, label=r["model"], color=c, alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels([m.replace("_"," ").title() for m in metrics])
    ax.set_ylim(0, 1.1); ax.set_ylabel("Score"); ax.set_title("Model Comparison", fontweight="bold")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, "model_comparison.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("[plots] model_comparison.png saved")


def plot_feature_importance(rf_model, feature_names):
    imp  = pd.Series(rf_model.feature_importances_, index=feature_names).sort_values()
    colors = plt.cm.RdYlGn(np.linspace(0.2, 0.9, len(imp)))
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(imp.index, imp.values, color=colors)
    ax.set_title("Feature Importance — Random Forest", fontweight="bold")
    ax.set_xlabel("Importance")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, "feature_importance.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("[plots] feature_importance.png saved")


# ── main pipeline ─────────────────────────────────────────────────────────────

def run():
    print("\n" + "="*55)
    print("  CardioShield AI — Training Pipeline")
    print("="*55)

    # Data
    df = clean(load_raw(), save=True)
    X_tr, X_te, y_tr, y_te, scaler = split_and_scale(df)

    # Model definitions + grids
    configs = [
        ("logistic_regression",
         LogisticRegression(max_iter=1000, random_state=42),
         {"C": [0.01, 0.1, 1.0, 10.0], "solver": ["lbfgs","liblinear"]}),
        ("decision_tree",
         DecisionTreeClassifier(random_state=42),
         {"max_depth": [3,5,7,None], "criterion":["gini","entropy"], "min_samples_split":[2,5,10]}),
        ("random_forest",
         RandomForestClassifier(random_state=42, n_jobs=-1),
         {"n_estimators":[100,200], "max_depth":[5,10,None], "min_samples_split":[2,5]}),
    ]

    results = []
    rf_model = None

    for fname, estimator, grid in configs:
        display = fname.replace("_", " ").title()
        print(f"\n  ▶ {display}")
        gs = GridSearchCV(estimator, grid, cv=CV, scoring="roc_auc", n_jobs=-1, verbose=0)
        gs.fit(X_tr, y_tr)
        best = gs.best_estimator_
        print(f"    Best params: {gs.best_params_}")
        r = evaluate(display, best, X_te, y_te)
        print(f"    Accuracy={r['accuracy']:.4f}  AUC={r['roc_auc']:.4f}  F1={r['f1_score']:.4f}")
        results.append(r)
        save_model(fname, best)
        if fname == "random_forest":
            rf_model = best

    # Neural Network (simple MLP via sklearn)
    from sklearn.neural_network import MLPClassifier
    print("\n  ▶ Neural Network (MLP)")
    nn = MLPClassifier(hidden_layer_sizes=(64,32,16), activation="relu", max_iter=500,
                       early_stopping=True, random_state=42)
    nn.fit(X_tr, y_tr)
    r_nn = evaluate("Neural Network", nn, X_te, y_te)
    print(f"    Accuracy={r_nn['accuracy']:.4f}  AUC={r_nn['roc_auc']:.4f}  F1={r_nn['f1_score']:.4f}")
    results.append(r_nn)
    save_model("neural_network", nn)

    # Plots
    print("\n  ▶ Generating reports…")
    plot_confusion_matrices(results, y_te)
    plot_roc_curves(results, y_te)
    plot_metrics_comparison(results)
    if rf_model:
        plot_feature_importance(rf_model, FEATURE_COLS)

    # Save metrics CSV
    rows = [{k: v for k, v in r.items() if k not in ("y_pred","y_prob","cm")}
            for r in results]
    df_m = pd.DataFrame(rows).set_index("model")
    df_m.to_csv(os.path.join(REPORTS_DIR, "performance_metrics.csv"))
    print(f"  ▶ performance_metrics.csv saved")

    # Save best model name
    best_model = df_m["roc_auc"].idxmax().lower().replace(" ","_")
    with open(os.path.join(MODELS_DIR, "best_model.txt"), "w") as f:
        f.write(best_model)
    print(f"\n  ✅ Best model: {best_model}")
    print("="*55 + "\n")
    return df_m


if __name__ == "__main__":
    run()
