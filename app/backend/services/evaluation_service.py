from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from app.backend.database.models import db, Patient, Prediction

def get_model_metrics():
    """
    Calculate and return metrics for all models based on patients with actual_outcome recorded.
    """
    # Fetch patients with actual outcomes
    patients = Patient.query.filter(Patient.actual_outcome.isnot(None)).all()
    if not patients:
        return {}

    patient_ids = [p.id for p in patients]
    
    # Mapping patient_id to actual outcome
    actual_outcomes = {p.id: p.actual_outcome for p in patients}

    # Fetch predictions for these patients
    predictions = Prediction.query.filter(Prediction.patient_id.in_(patient_ids)).all()

    # Group predictions by model
    model_data = {}
    for pred in predictions:
        model = pred.model_used
        if model not in model_data:
            model_data[model] = {'y_true': [], 'y_pred': [], 'y_prob': []}
        
        model_data[model]['y_true'].append(actual_outcomes[pred.patient_id])
        model_data[model]['y_pred'].append(pred.prediction)
        model_data[model]['y_prob'].append(pred.probability)

    # Calculate metrics
    metrics = {}
    for model, data in model_data.items():
        y_true = data['y_true']
        y_pred = data['y_pred']
        y_prob = data['y_prob']
        
        # If there's only one class present in y_true, ROC-AUC cannot be calculated
        import numpy as np
        try:
            roc_auc = roc_auc_score(y_true, y_prob)
            if np.isnan(roc_auc):
                roc_auc = None
        except ValueError:
            roc_auc = None
            
        metrics[model] = {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, zero_division=0)),
            'f1_score': float(f1_score(y_true, y_pred, zero_division=0)),
            'roc_auc': float(roc_auc) if roc_auc is not None else None,
            'samples': len(y_true)
        }

    return metrics
