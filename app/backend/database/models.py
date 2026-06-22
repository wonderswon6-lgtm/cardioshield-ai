"""
models.py — SQLAlchemy ORM models.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Patient(db.Model):
    __tablename__ = "patients"
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(120))
    age      = db.Column(db.Integer,  nullable=False)
    sex      = db.Column(db.Integer,  nullable=False)
    cp       = db.Column(db.Integer,  nullable=False)
    trestbps = db.Column(db.Float,    nullable=False)
    chol     = db.Column(db.Float,    nullable=False)
    fbs      = db.Column(db.Integer,  nullable=False)
    restecg  = db.Column(db.Integer,  nullable=False)
    thalach  = db.Column(db.Float,    nullable=False)
    exang    = db.Column(db.Integer,  nullable=False)
    oldpeak  = db.Column(db.Float,    nullable=False)
    slope    = db.Column(db.Integer,  nullable=False)
    ca       = db.Column(db.Integer,  nullable=False)
    thal     = db.Column(db.Integer,  nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    predictions = db.relationship("Prediction", backref="patient",
                                  lazy=True, cascade="all, delete-orphan")
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Prediction(db.Model):
    __tablename__ = "predictions"
    id           = db.Column(db.Integer, primary_key=True)
    patient_id   = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    model_used   = db.Column(db.String(50), default="random_forest")
    prediction   = db.Column(db.Integer,  nullable=False)   # 0 or 1
    probability  = db.Column(db.Float,    nullable=False)
    confidence   = db.Column(db.Float,    nullable=False)
    risk_level   = db.Column(db.String(20), nullable=False)  # Low | Moderate | High
    recommendation = db.Column(db.Text)
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ModelMetric(db.Model):
    __tablename__ = "model_metrics"
    id          = db.Column(db.Integer, primary_key=True)
    model_name  = db.Column(db.String(50), nullable=False)
    accuracy    = db.Column(db.Float)
    precision   = db.Column(db.Float)
    recall      = db.Column(db.Float)
    f1_score    = db.Column(db.Float)
    roc_auc     = db.Column(db.Float)
    specificity = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
