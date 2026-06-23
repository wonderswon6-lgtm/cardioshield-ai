"""
cdss_service.py — Backend service for the Clinical Decision Support System.
"""
from app.backend.database.models import db, Doctor, Patient, Consultation, Prediction


# ── Doctor Auth ───────────────────────────────────────────────────────────────

def get_doctor_by_credentials(doctor_id: str, password: str):
    """Return Doctor object if credentials match, else None."""
    doc = Doctor.query.filter_by(doctor_id=doctor_id.strip().upper()).first()
    if doc and doc.check_password(password):
        return doc
    return None


def get_doctor_by_id(doctor_pk: int):
    return Doctor.query.get(doctor_pk)


def seed_demo_doctor():
    """Create a demo doctor account if no doctors exist."""
    if Doctor.query.count() == 0:
        d = Doctor(doctor_id="DR-001", name="Dr. Sarah Mitchell",
                   specialization="Cardiologist")
        d.set_password("doctor123")
        db.session.add(d)
        db.session.commit()


# ── Patient Search ────────────────────────────────────────────────────────────

def search_patients(query: str, limit: int = 20) -> list:
    """Full-text search on patient name or ID."""
    q = query.strip()
    results = []
    if q.isdigit():
        p = Patient.query.get(int(q))
        if p:
            results = [p]
    if not results:
        results = (Patient.query
                   .filter(Patient.name.ilike(f"%{q}%"))
                   .order_by(Patient.created_at.desc())
                   .limit(limit)
                   .all())
    if not results:
        results = Patient.query.order_by(Patient.created_at.desc()).limit(limit).all()
    return results


def get_patient_with_history(patient_id: int) -> dict:
    """Return patient details along with past consultations and predictions."""
    patient = Patient.query.get(patient_id)
    if not patient:
        return {}

    preds = (Prediction.query
             .filter_by(patient_id=patient_id)
             .order_by(Prediction.predicted_at.desc())
             .all())

    consultations = (Consultation.query
                     .filter_by(patient_id=patient_id)
                     .order_by(Consultation.created_at.desc())
                     .all())

    # Aggregate average risk from predictions
    if preds:
        avg_prob = sum(p.probability for p in preds) / len(preds)
        risk_level = "High" if avg_prob >= 65 else ("Moderate" if avg_prob >= 35 else "Low")
    else:
        avg_prob = None
        risk_level = None

    return {
        "patient": patient,
        "predictions": preds,
        "consultations": consultations,
        "avg_risk": round(avg_prob, 1) if avg_prob is not None else None,
        "risk_level": risk_level,
    }


# ── Consultation ──────────────────────────────────────────────────────────────

def create_consultation(doctor_id: int, patient_id: int, chief_complaint: str = "") -> Consultation:
    c = Consultation(doctor_id=doctor_id, patient_id=patient_id,
                     chief_complaint=chief_complaint, status="Open")
    db.session.add(c)
    db.session.commit()
    return c


def save_consultation_report(consultation_id: int, notes: str,
                              prediction_id: int = None, status: str = "Closed") -> bool:
    c = Consultation.query.get(consultation_id)
    if not c:
        return False
    c.doctor_notes = notes
    c.status = status
    if prediction_id:
        c.prediction_id = prediction_id
    db.session.commit()
    return True


def get_consultation(consultation_id: int):
    return Consultation.query.get(consultation_id)
