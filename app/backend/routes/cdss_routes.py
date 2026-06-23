"""
cdss_routes.py — Flask Blueprint for the Clinical Decision Support System.
"""
from flask import (Blueprint, request, jsonify, render_template,
                   redirect, url_for, session, flash)

cdss_bp = Blueprint("cdss", __name__, url_prefix="/cdss")

FEATURE_COLS = ["age","sex","cp","trestbps","chol","fbs","restecg",
                "thalach","exang","oldpeak","slope","ca","thal"]


def doctor_required(f):
    """Decorator: redirects to login if doctor not in session."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "doctor_id" not in session:
            return redirect(url_for("cdss.login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth ──────────────────────────────────────────────────────────────────────

@cdss_bp.route("/login", methods=["GET", "POST"])
def login():
    from app.backend.services.cdss_service import get_doctor_by_credentials, seed_demo_doctor
    seed_demo_doctor()

    if request.method == "POST":
        did   = request.form.get("doctor_id", "").strip()
        pwd   = request.form.get("password", "")
        doc   = get_doctor_by_credentials(did, pwd)
        if doc:
            session["doctor_id"]   = doc.id
            session["doctor_name"] = doc.name
            session["doctor_spec"] = doc.specialization
            return redirect(url_for("cdss.patient_search"))
        flash("Invalid Doctor ID or password.", "error")

    return render_template("cdss/login.html")


@cdss_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("cdss.login"))


# ── Patient Search ─────────────────────────────────────────────────────────────

@cdss_bp.route("/patients", methods=["GET"])
@doctor_required
def patient_search():
    from app.backend.services.cdss_service import search_patients
    query   = request.args.get("q", "")
    patients = search_patients(query) if query else []
    # If no query, show recent patients
    from app.backend.database.models import Patient
    recent = Patient.query.order_by(Patient.created_at.desc()).limit(10).all()
    return render_template("cdss/patient_search.html",
                           patients=patients, query=query, recent=recent)


@cdss_bp.route("/new_patient", methods=["GET", "POST"])
@doctor_required
def new_patient():
    if request.method == "GET":
        return render_template("cdss/new_patient.html")

    from app.backend.services.db_service import create_patient
    from app.backend.services.prediction_service import predict, models_trained, get_available_models
    from app.backend.services.explanation_service import explain_prediction
    from app.backend.services.db_service import save_prediction

    # Collect all clinical fields
    try:
        data = {
            "name":      request.form.get("name", "Unnamed Patient"),
            "age":       int(float(request.form.get("age", 50))),
            "sex":       int(float(request.form.get("sex", 1))),
            "cp":        int(float(request.form.get("cp", 0))),
            "trestbps":  int(float(request.form.get("trestbps", 120))),
            "chol":      int(float(request.form.get("chol", 200))),
            "fbs":       int(float(request.form.get("fbs", 0))),
            "restecg":   int(float(request.form.get("restecg", 0))),
            "thalach":   int(float(request.form.get("thalach", 150))),
            "exang":     int(float(request.form.get("exang", 0))),
            "oldpeak":   float(request.form.get("oldpeak", 0.0)),
            "slope":     int(float(request.form.get("slope", 1))),
            "ca":        int(float(request.form.get("ca", 0))),
            "thal":      int(float(request.form.get("thal", 2))),
        }
    except (ValueError, TypeError) as e:
        flash(f"Invalid input: {e}", "error")
        return redirect(url_for("cdss.new_patient"))

    # Save patient
    p = create_patient(data)

    # Run predictions if models are available
    if models_trained():
        feature_cols = ["age","sex","cp","trestbps","chol","fbs","restecg",
                        "thalach","exang","oldpeak","slope","ca","thal"]
        patient_data = {f: float(data[f]) for f in feature_cols}
        for m_name in get_available_models():
            try:
                res = predict(patient_data, m_name)
                res["feature_contributions"] = explain_prediction(patient_data, m_name)
                save_prediction(p.id, res)
            except Exception:
                continue

    flash(f"Patient {p.name} registered and predictions run.", "success")
    return redirect(url_for("cdss.consultation", patient_id=p.id))


# ── Consultation ───────────────────────────────────────────────────────────────

@cdss_bp.route("/consult/<int:patient_id>", methods=["GET"])
@doctor_required
def consultation(patient_id):
    from app.backend.services.cdss_service import (
        get_patient_with_history, create_consultation
    )
    data = get_patient_with_history(patient_id)
    if not data:
        flash("Patient not found.", "error")
        return redirect(url_for("cdss.patient_search"))

    # Create a new consultation session
    c = create_consultation(
        doctor_id=session["doctor_id"],
        patient_id=patient_id,
        chief_complaint=request.args.get("complaint", "")
    )
    return render_template("cdss/consultation.html",
                           patient=data["patient"],
                           predictions=data["predictions"],
                           consultations=data["consultations"],
                           avg_risk=data["avg_risk"],
                           risk_level=data["risk_level"],
                           consultation_id=c.id)


# ── API: Run Prediction ───────────────────────────────────────────────────────

@cdss_bp.route("/api/predict", methods=["POST"])
@doctor_required
def cdss_predict():
    data = request.get_json(force=True, silent=True) or {}
    missing = [f for f in FEATURE_COLS if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    from app.backend.services.prediction_service import predict, models_trained, get_available_models
    from app.backend.services.explanation_service import explain_prediction
    from app.backend.services.db_service import save_prediction

    if not models_trained():
        return jsonify({"error": "Models not trained. Run: python main.py --train"}), 503

    patient_data = {f: float(data[f]) for f in FEATURE_COLS}
    patient_id   = int(data.get("patient_id", 0)) or None
    models       = get_available_models()

    all_preds = []
    last_pred_id = None

    for m_name in models:
        try:
            res = predict(patient_data, m_name)
            res["feature_contributions"] = explain_prediction(patient_data, m_name)
            if patient_id:
                pred_rec = save_prediction(patient_id, res)
                res["prediction_id"] = pred_rec.id
                last_pred_id = pred_rec.id
            all_preds.append(res)
        except Exception as e:
            continue

    if not all_preds:
        return jsonify({"error": "All predictions failed."}), 500

    # Ensemble: average probability across models
    avg_prob = sum(p["probability"] for p in all_preds) / len(all_preds)
    avg_pred = 1 if avg_prob >= 50 else 0
    risk_level = "High" if avg_prob >= 65 else ("Moderate" if avg_prob >= 35 else "Low")

    # Best explanation: use random_forest contributions
    rf_result = next((p for p in all_preds if p["model_used"] == "random_forest"), all_preds[0])
    contributions = rf_result.get("feature_contributions", [])

    # Build AI recommendations based on risk factors + clinical values
    recommendations = _build_recommendations(patient_data, avg_prob, contributions)

    return jsonify({
        "status": "ok",
        "ensemble_prob": round(avg_prob, 1),
        "ensemble_pred": avg_pred,
        "risk_level": risk_level,
        "last_prediction_id": last_pred_id,
        "per_model": [{"model": p["model_used"], "prob": p["probability"],
                       "pred": p["prediction"], "risk": p["risk_level"]} for p in all_preds],
        "contributions": contributions[:6],
        "recommendations": recommendations,
    })


# ── API: Save Consultation Report ─────────────────────────────────────────────

@cdss_bp.route("/api/consultation/<int:cid>/save", methods=["POST"])
@doctor_required
def save_report(cid):
    data = request.get_json(force=True, silent=True) or {}
    from app.backend.services.cdss_service import save_consultation_report
    ok = save_consultation_report(
        consultation_id=cid,
        notes=data.get("notes", ""),
        prediction_id=data.get("prediction_id"),
        status="Closed"
    )
    return jsonify({"status": "success" if ok else "error"})


# ── API: Patient search (JSON for autocomplete) ───────────────────────────────

@cdss_bp.route("/api/patients/search")
@doctor_required
def api_patient_search():
    from app.backend.services.cdss_service import search_patients
    q = request.args.get("q", "")
    patients = search_patients(q, limit=10)
    return jsonify({"patients": [{"id": p.id, "name": p.name or f"Patient #{p.id}",
                                  "age": p.age, "sex": "M" if p.sex==1 else "F"} for p in patients]})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_recommendations(data: dict, prob: float, contributions: list) -> list:
    recs = []
    top_features = {c["feature"] for c in contributions[:4] if c["contribution"] > 2}

    if prob >= 65:
        recs.append({"priority": "urgent", "icon": "🚨",
                     "text": "Immediate cardiology consultation strongly advised."})
        recs.append({"priority": "urgent", "icon": "🏥",
                     "text": "Consider hospital admission for further evaluation."})
    elif prob >= 35:
        recs.append({"priority": "moderate", "icon": "⚠️",
                     "text": "Schedule cardiology follow-up within 2 weeks."})

    if data.get("chol", 0) > 240 or "chol" in top_features:
        recs.append({"priority": "info", "icon": "💊",
                     "text": "Lipid-lowering therapy (statin) evaluation recommended."})
    if data.get("trestbps", 0) > 140 or "trestbps" in top_features:
        recs.append({"priority": "info", "icon": "🩺",
                     "text": "Blood pressure management and monitoring required."})
    if data.get("restecg", 0) in [1, 2] or "restecg" in top_features:
        recs.append({"priority": "moderate", "icon": "📋",
                     "text": "12-lead ECG and Holter monitoring recommended."})
    if data.get("exang", 0) == 1 or "exang" in top_features:
        recs.append({"priority": "moderate", "icon": "🏃",
                     "text": "Stress echocardiography or treadmill test advised."})
    if data.get("oldpeak", 0) > 2.0 or "oldpeak" in top_features:
        recs.append({"priority": "moderate", "icon": "📈",
                     "text": "ST-segment monitoring and coronary angiography considered."})
    if data.get("ca", 0) >= 2:
        recs.append({"priority": "urgent", "icon": "🔬",
                     "text": "Significant vessel involvement — angiography advised."})
    if data.get("fbs", 0) == 1:
        recs.append({"priority": "info", "icon": "🩸",
                     "text": "Diabetes management and HbA1c testing recommended."})

    if prob < 35:
        recs.append({"priority": "info", "icon": "✅",
                     "text": "Low cardiac risk. Lifestyle modifications and annual review advised."})

    return recs[:6]
