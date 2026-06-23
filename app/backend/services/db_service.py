"""
db_service.py — CRUD operations using SQLAlchemy ORM.
"""
import os, csv
from datetime import datetime
from app.backend.database.models import db, Patient, Prediction, ModelMetric

BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


# ── Patients ──────────────────────────────────────────────────────────────────

def create_patient(data: dict) -> Patient:
    fields = {c.name for c in Patient.__table__.columns} - {"id","created_at"}
    p = Patient(**{k: v for k, v in data.items() if k in fields})
    db.session.add(p); db.session.commit()
    return p

def get_patient(pid: int): return Patient.query.get(pid)
def all_patients(limit=200): return Patient.query.order_by(Patient.created_at.desc()).limit(limit).all()
def delete_patient(pid: int):
    p = Patient.query.get(pid)
    if p: db.session.delete(p); db.session.commit(); return True
    return False


# ── Predictions ───────────────────────────────────────────────────────────────

def save_prediction(patient_id: int, result: dict) -> Prediction:
    pred = Prediction(
        patient_id     = patient_id,
        model_used     = result["model_used"],
        prediction     = result["prediction"],
        probability    = result["probability"],
        confidence     = result["confidence"],
        risk_level     = result["risk_level"],
        recommendation = result["recommendation"],
    )
    db.session.add(pred); db.session.commit()
    return pred

def recent_predictions(limit=50):
    from collections import defaultdict
    # Query all predictions ordered by predicted_at desc
    all_preds = (Prediction.query
                 .join(Patient, Prediction.patient_id == Patient.id)
                 .order_by(Prediction.predicted_at.desc())
                 .all())
                 
    grouped = []
    seen_patients = set()
    patient_preds = defaultdict(list)
    
    for p in all_preds:
        patient_preds[p.patient_id].append(p)
        
    for p in all_preds:
        if p.patient_id not in seen_patients:
            seen_patients.add(p.patient_id)
            p_preds = patient_preds[p.patient_id]
            
            avg_prob = sum(x.probability for x in p_preds) / len(p_preds)
            avg_pred = 1 if (sum(x.prediction for x in p_preds) / len(p_preds)) >= 0.5 else 0
            if avg_prob < 35.0:
                risk = "Low"
            elif avg_prob < 65.0:
                risk = "Moderate"
            else:
                risk = "High"
                
            d = p_preds[0].to_dict()
            d["model_used"] = "All 4 Models"
            d["probability"] = round(avg_prob, 2)
            d["prediction"] = avg_pred
            d["risk_level"] = risk
            d["patient_name"] = p_preds[0].patient.name if p_preds[0].patient else ""
            d["actual_outcome"] = p_preds[0].patient.actual_outcome if p_preds[0].patient else None
            d["patient_data"] = p_preds[0].patient.to_dict() if p_preds[0].patient else {}
            
            grouped.append(d)
            if len(grouped) >= limit:
                break
                
    return grouped

def get_stats() -> dict:
    from collections import defaultdict
    preds = Prediction.query.all()
    
    patient_groups = defaultdict(list)
    for p in preds:
        patient_groups[p.patient_id].append(p)
        
    total = len(patient_groups)
    disease = 0
    high = 0
    mod = 0
    low = 0
    
    for pid, p_preds in patient_groups.items():
        if not p_preds:
            continue
        avg_prob = sum(x.probability for x in p_preds) / len(p_preds)
        avg_pred = 1 if (sum(x.prediction for x in p_preds) / len(p_preds)) >= 0.5 else 0
        
        if avg_pred == 1:
            disease += 1
            
        if avg_prob < 35.0:
            low += 1
        elif avg_prob < 65.0:
            mod += 1
        else:
            high += 1
            
    return dict(total=total, disease=disease, no_disease=total-disease,
                high_risk=high, moderate_risk=mod, low_risk=low,
                disease_rate=round(disease/total*100,1) if total else 0)


# ── Model Metrics ─────────────────────────────────────────────────────────────

def upsert_metrics(metrics_list: list):
    """Insert latest model metrics from training."""
    for m in metrics_list:
        db.session.add(ModelMetric(**m))
    db.session.commit()

def load_metrics_from_csv():
    """Load metrics from reports/performance_metrics.csv into DB."""
    path = os.path.join(REPORTS_DIR, "performance_metrics.csv")
    if not os.path.exists(path): return
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.session.add(ModelMetric(
                model_name  = row.get("model",""),
                accuracy    = float(row.get("accuracy",0)),
                precision   = float(row.get("precision",0)),
                recall      = float(row.get("recall",0)),
                f1_score    = float(row.get("f1_score",0)),
                roc_auc     = float(row.get("roc_auc",0)),
                specificity = float(row.get("specificity",0)),
            ))
    db.session.commit()

def get_all_metrics():
    """Return latest metric per model."""
    from sqlalchemy import func
    sub = (db.session.query(
               ModelMetric.model_name,
               func.max(ModelMetric.recorded_at).label("latest"))
           .group_by(ModelMetric.model_name).subquery())
    return (ModelMetric.query
            .join(sub, (ModelMetric.model_name == sub.c.model_name) &
                       (ModelMetric.recorded_at == sub.c.latest))
            .all())
