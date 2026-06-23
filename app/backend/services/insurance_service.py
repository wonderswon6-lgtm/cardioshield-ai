"""
insurance_service.py — Data service for Insurance Risk Assessment Dashboard.
"""
import os, csv
from collections import defaultdict
from app.backend.database.models import db, Patient, Prediction, ModelMetric


def get_insurance_kpis() -> dict:
    """Returns KPI counts for the insurance dashboard."""
    preds = Prediction.query.all()

    patient_groups = defaultdict(list)
    for p in preds:
        patient_groups[p.patient_id].append(p)

    total = len(patient_groups)
    low = mod = high = 0

    for pid, p_preds in patient_groups.items():
        avg_prob = sum(x.probability for x in p_preds) / len(p_preds)
        if avg_prob < 35.0:
            low += 1
        elif avg_prob < 70.0:
            mod += 1
        else:
            high += 1

    return {
        "total": total,
        "low_risk": low,
        "medium_risk": mod,
        "high_risk": high,
    }


def get_insurance_applicants(limit=50) -> list:
    """Returns a list of all applicants with aggregated risk data."""
    all_preds = (Prediction.query
                 .join(Patient, Prediction.patient_id == Patient.id)
                 .order_by(Prediction.predicted_at.desc())
                 .all())

    patient_groups = defaultdict(list)
    patient_order = []
    for p in all_preds:
        if p.patient_id not in patient_groups:
            patient_order.append(p.patient_id)
        patient_groups[p.patient_id].append(p)

    applicants = []
    for pid in patient_order[:limit]:
        p_preds = patient_groups[pid]
        patient = p_preds[0].patient
        avg_prob = sum(x.probability for x in p_preds) / len(p_preds)
        avg_pred = 1 if (sum(x.prediction for x in p_preds) / len(p_preds)) >= 0.5 else 0

        if avg_prob < 35.0:
            risk_cat = "Low"
            premium = "Standard Plan"
            action = "No further action required."
            badge = "success"
        elif avg_prob < 70.0:
            risk_cat = "Medium"
            premium = "Medium Premium Plan"
            action = "Annual cardiac check-up recommended."
            badge = "warning"
        else:
            risk_cat = "High"
            premium = "High Premium Plan"
            action = "Immediate medical evaluation required."
            badge = "danger"

        # Claim probability is modeled as risk * 0.9 (correlation factor)
        claim_prob = round(min(avg_prob * 0.90, 100), 1)

        applicants.append({
            "applicant_id": f"INS-{pid:04d}",
            "patient_id": pid,
            "name": patient.name or f"Patient #{pid}",
            "age": patient.age,
            "sex": "Male" if patient.sex == 1 else "Female",
            "prediction": avg_pred,
            "risk_score": round(avg_prob, 1),
            "claim_prob": claim_prob,
            "risk_category": risk_cat,
            "premium": premium,
            "action": action,
            "badge": badge,
            # Clinical data for risk factor display
            "chol": patient.chol,
            "trestbps": patient.trestbps,
            "thalach": patient.thalach,
            "cp": patient.cp,
            "oldpeak": patient.oldpeak,
            "age_val": patient.age,
        })

    return applicants


def get_insurance_risk_factors(patient_id: int) -> list:
    """Get top risk factors for a specific patient using ML explanation."""
    try:
        from app.backend.services.explanation_service import explain_prediction
        from app.backend.database.models import Patient as P
        patient = P.query.get(patient_id)
        if not patient:
            return []
        data = {c.name: getattr(patient, c.name)
                for c in patient.__table__.columns
                if c.name not in ("id", "name", "created_at", "actual_outcome")}
        contribs = explain_prediction(data, "random_forest")
        return contribs[:6]  # top 6 factors
    except Exception:
        return []


def get_risk_distribution() -> dict:
    """Returns data for the risk distribution doughnut chart."""
    kpis = get_insurance_kpis()
    return {
        "labels": ["Low Risk", "Medium Risk", "High Risk"],
        "data": [kpis["low_risk"], kpis["medium_risk"], kpis["high_risk"]],
        "colors": ["#22c55e", "#eab308", "#ef4444"]
    }
