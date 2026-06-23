import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.backend.app import create_app
from app.backend.services.db_service import get_all_metrics

app = create_app()
with app.app_context():
    metrics = get_all_metrics()
    for m in metrics:
        print(f"{m.model_name}: {m.recorded_at} (ID: {m.id})")
