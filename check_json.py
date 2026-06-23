import sys, os, json, math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.backend.app import create_app
from app.backend.services.evaluation_service import get_model_metrics
from flask import jsonify

app = create_app()
with app.app_context():
    metrics = get_model_metrics()
    print("Raw metrics:")
    print(metrics)
    
    # Try to serialize
    import json
    try:
        print("\nJSON Serialization:")
        print(json.dumps(metrics))
    except Exception as e:
        print("JSON dumps error:", e)
