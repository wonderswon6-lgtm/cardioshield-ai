import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.backend.app import create_app
from app.backend.database.models import db, ModelMetric
from app.backend.services.db_service import load_metrics_from_csv

app = create_app()
with app.app_context():
    # Delete all
    ModelMetric.query.delete()
    db.session.commit()
    print("Deleted all model metrics.")
    
    # Reload from CSV
    load_metrics_from_csv()
    print("Reloaded metrics from CSV.")
    
    # Print what we have now
    for m in ModelMetric.query.all():
        print(f"{m.model_name}: {m.recorded_at} (ID: {m.id})")
