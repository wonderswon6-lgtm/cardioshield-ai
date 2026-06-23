"""
app.py — Flask application factory.
"""
import os
from flask import Flask
from flask_cors import CORS
from app.backend.config import get_config
from app.backend.database.models import db
from app.backend.routes.routes import main_bp
from app.backend.routes.cdss_routes import cdss_bp


def create_app(env: str = None) -> Flask:
    cfg = get_config(env)

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "static"),
    )
    app.config.from_object(cfg)
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    CORS(app)
    db.init_app(app)
    app.register_blueprint(main_bp)
    app.register_blueprint(cdss_bp)

    with app.app_context():
        db.create_all()
        # Auto-load metrics from CSV if DB is empty
        try:
            from app.backend.database.models import ModelMetric
            if ModelMetric.query.count() == 0:
                from app.backend.services.db_service import load_metrics_from_csv
                load_metrics_from_csv()
        except Exception:
            pass

    return app

