"""
routes.py — All Flask routes in one file (API + Pages).
"""
import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for

main_bp = Blueprint("main", __name__)

FEATURE_COLS = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"]


# ════════════════════════════════════════════════════════════
# PAGE ROUTES
# ════════════════════════════════════════════════════════════

@main_bp.route("/")
def home():
    return render_template("home.html")

@main_bp.route("/predict")
def predict_page():
    return render_template("prediction.html")

@main_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@main_bp.route("/result")
def result_page():
    return render_template("result.html")


@main_bp.route("/insurance-dashboard")
def insurance_dashboard_page():
    from app.backend.services.insurance_service import (
        get_insurance_kpis, get_insurance_applicants, get_risk_distribution
    )
    kpis        = get_insurance_kpis()
    applicants  = get_insurance_applicants(limit=50)
    dist        = get_risk_distribution()
    return render_template(
        "insurance_dashboard.html",
        kpis=kpis,
        applicants=applicants,
        dist=dist,
    )


@main_bp.route("/api/insurance/patient/<int:patient_id>/risk-factors")
def api_insurance_risk_factors(patient_id):
    from app.backend.services.insurance_service import get_insurance_risk_factors
    try:
        factors = get_insurance_risk_factors(patient_id)
        return jsonify({"status": "ok", "factors": factors}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ════════════════════════════════════════════════════════════
# API — PREDICTION
# ════════════════════════════════════════════════════════════

@main_bp.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(force=True, silent=True) or {}
    missing = [f for f in FEATURE_COLS if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    from app.backend.services.prediction_service import predict, models_trained, get_available_models
    if not models_trained():
        return jsonify({"error": "Models not trained yet. Run: python main.py --train"}), 503

    patient_data = {f: float(data[f]) for f in FEATURE_COLS}
    models = get_available_models()
    
    predictions = []
    patient_id = None
    patient_name = data.get("name", "")
    
    # Save patient details once
    try:
        from app.backend.services.db_service import create_patient, save_prediction
        p_data = {**patient_data, "name": patient_name}
        patient = create_patient(p_data)
        patient_id = patient.id
    except Exception as db_err:
        return jsonify({"error": f"Database error: {str(db_err)}"}), 500

    # Predict with all models and persist predictions
    from app.backend.services.explanation_service import explain_prediction
    for m_name in models:
        try:
            res = predict(patient_data, m_name)
            res["feature_contributions"] = explain_prediction(patient_data, m_name)
            if patient_id:
                pred_rec = save_prediction(patient_id, res)
                res["prediction_id"] = pred_rec.id
            predictions.append(res)
        except Exception as e:
            pass

    if not predictions:
        return jsonify({"error": "All predictions failed."}), 500

    return jsonify({
        "status": "success",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "patient_age": int(patient_data["age"]),
        "patient_sex": "Male" if patient_data["sex"] == 1 else "Female",
        "predictions": predictions
    }), 200


# ════════════════════════════════════════════════════════════
# API — ANALYTICS
# ════════════════════════════════════════════════════════════

@main_bp.route("/api/analytics/stats")
def api_stats():
    try:
        from app.backend.services.db_service import get_stats
        return jsonify({"status": "ok", "data": get_stats()}), 200
    except Exception as e:
        return jsonify({"status": "ok", "data": {"total":0,"disease":0,"no_disease":0,
                        "high_risk":0,"moderate_risk":0,"low_risk":0,"disease_rate":0},
                        "warning": str(e)}), 200


@main_bp.route("/api/analytics/recent")
def api_recent():
    try:
        from app.backend.services.db_service import recent_predictions
        preds = recent_predictions(50)
        return jsonify({"status": "ok", "predictions": preds}), 200
    except Exception as e:
        return jsonify({"status": "ok", "predictions": [], "warning": str(e)}), 200


@main_bp.route("/api/analytics/metrics")
def api_metrics():
    try:
        from app.backend.services.db_service import get_all_metrics
        metrics = get_all_metrics()
        return jsonify({"status": "ok", "metrics": [m.to_dict() for m in metrics]}), 200
    except Exception as e:
        # Fallback: read CSV
        import csv, os
        BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        path = os.path.join(BASE, "reports", "performance_metrics.csv")
        rows = []
        if os.path.exists(path):
            with open(path) as f:
                rows = list(csv.DictReader(f))
        return jsonify({"status": "ok", "metrics": rows, "source": "csv"}), 200


@main_bp.route("/api/models")
def api_models():
    from app.backend.services.prediction_service import get_available_models
    return jsonify({"models": get_available_models()}), 200


@main_bp.route("/api/patients")
def api_patients():
    try:
        from app.backend.services.db_service import all_patients
        patients = all_patients()
        return jsonify({"patients": [p.to_dict() for p in patients]}), 200
    except Exception as e:
        return jsonify({"patients": [], "warning": str(e)}), 200


@main_bp.route("/api/patient/<int:patient_id>/predictions")
def api_patient_predictions(patient_id):
    try:
        from app.backend.database.models import Prediction
        from app.backend.services.explanation_service import explain_prediction
        preds = Prediction.query.filter_by(patient_id=patient_id).order_by(Prediction.predicted_at.desc()).all()
        predictions_data = []
        for p in preds:
            p_dict = p.to_dict()
            p_data = {col: getattr(p.patient, col) for col in FEATURE_COLS}
            p_dict["feature_contributions"] = explain_prediction(p_data, p.model_used)
            predictions_data.append(p_dict)
        return jsonify({"status": "ok", "predictions": predictions_data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route("/api/train", methods=["POST"])
def api_train():
    """Trigger model training (for admin use)."""
    import threading, sys
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    sys.path.insert(0, BASE)
    def _train():
        from src.train_models import run
        run()
    t = threading.Thread(target=_train, daemon=True)
    t.start()
    return jsonify({"status": "Training started in background"}), 202


@main_bp.route("/health")
def health():
    return jsonify({"status": "ok", "app": "CardioShield AI"}), 200


@main_bp.route("/api/prediction/<int:pred_id>", methods=["DELETE"])
def delete_prediction_endpoint(pred_id):
    try:
        from app.backend.database.models import db, Prediction, Patient
        pred = Prediction.query.get(pred_id)
        if not pred:
            return jsonify({"status": "error", "message": "Prediction not found"}), 404
        
        # Deleting the patient will cascade delete all predictions for this patient
        patient = Patient.query.get(pred.patient_id)
        if patient:
            db.session.delete(patient)
        else:
            db.session.delete(pred)
        db.session.commit()
        return jsonify({"status": "success", "message": f"Prediction {pred_id} deleted."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route("/api/prediction/<int:pred_id>", methods=["PUT"])
def update_prediction_endpoint(pred_id):
    try:
        from app.backend.database.models import db, Prediction, Patient
        from app.backend.services.prediction_service import RECOMMENDATIONS
        
        data = request.get_json(force=True, silent=True) or {}
        pred = Prediction.query.get(pred_id)
        if not pred:
            return jsonify({"status": "error", "message": "Prediction not found"}), 404

        patient_name = data.get("patient_name")
        risk_level = data.get("risk_level")

        if patient_name is not None and pred.patient:
            pred.patient.name = patient_name
            
        if risk_level is not None:
            if risk_level not in RECOMMENDATIONS:
                return jsonify({"status": "error", "message": "Invalid risk level"}), 400
            
            # Update risk level and recommendation for ALL predictions of this patient
            sibling_preds = Prediction.query.filter_by(patient_id=pred.patient_id).all()
            for sp in sibling_preds:
                sp.risk_level = risk_level
                sp.recommendation = RECOMMENDATIONS[risk_level]
            
        db.session.commit()
        return jsonify({"status": "success", "message": f"Prediction {pred_id} updated successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route("/api/predictions/bulk", methods=["DELETE"])
def bulk_delete_predictions():
    try:
        from app.backend.database.models import db, Prediction, Patient
        data = request.get_json(force=True, silent=True) or {}
        ids = data.get("ids", [])
        if not ids:
            return jsonify({"status": "error", "message": "No IDs provided"}), 400
            
        # Get patient IDs for these predictions to delete patients (cascades to predictions)
        preds = Prediction.query.filter(Prediction.id.in_(ids)).all()
        patient_ids = list({p.patient_id for p in preds if p.patient_id})
        
        if patient_ids:
            Patient.query.filter(Patient.id.in_(patient_ids)).delete(synchronize_session=False)
        else:
            # Fallback to delete prediction records directly
            Prediction.query.filter(Prediction.id.in_(ids)).delete(synchronize_session=False)
            
        db.session.commit()
        return jsonify({"status": "success", "message": f"Deleted {len(ids)} predictions."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route("/api/evaluation/metrics")
def api_evaluation_metrics():
    try:
        from app.backend.services.evaluation_service import get_model_metrics
        metrics = get_model_metrics()
        return jsonify({"status": "ok", "metrics": metrics}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route("/api/patient/<int:patient_id>/outcome", methods=["PUT"])
def update_patient_outcome(patient_id):
    try:
        from app.backend.database.models import db, Patient
        data = request.get_json(force=True, silent=True) or {}
        outcome = data.get("actual_outcome")
        
        if outcome not in [0, 1]:
            return jsonify({"status": "error", "message": "Invalid outcome value. Must be 0 or 1."}), 400
            
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
            
        patient.actual_outcome = outcome
        db.session.commit()
        
        return jsonify({"status": "success", "message": f"Patient {patient_id} actual outcome updated."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
