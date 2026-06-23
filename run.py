"""
run.py — Quick Flask server launcher (models must be trained first).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.backend.app import create_app

app = create_app(env=os.environ.get("FLASK_ENV", "development"))

# Auto-migrate database on Render or startup
with app.app_context():
    from app.backend.database.models import db
    from sqlalchemy import text
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE patients ADD COLUMN actual_outcome SMALLINT DEFAULT NULL;"))
            conn.commit()
            print("DB Migration: Column 'actual_outcome' added successfully.")
    except Exception as e:
        if 'already exists' not in str(e):
            print("DB Migration Error:", e)

if __name__ == "__main__":
    host  = os.environ.get("FLASK_HOST", "127.0.0.1")
    port  = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    print(f"\n  CardioShield AI  →  http://{host}:{port}\n")
    app.run(host=host, port=port, debug=debug, use_reloader=False)
