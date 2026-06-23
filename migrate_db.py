import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.backend.app import create_app
from app.backend.database.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if the column already exists
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE patients ADD COLUMN actual_outcome SMALLINT DEFAULT NULL;"))
            conn.commit()
            print("Column 'actual_outcome' added successfully.")
    except Exception as e:
        if 'already exists' in str(e):
            print("Column 'actual_outcome' already exists.")
        else:
            print("Error:", e)
