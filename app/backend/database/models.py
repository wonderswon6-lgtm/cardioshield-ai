"""
models.py — SQLAlchemy ORM models.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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
    thal = db.Column(db.Integer,  nullable=False)
    actual_outcome = db.Column(db.SmallInteger, nullable=True)
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


class Doctor(db.Model):
    __tablename__ = "doctors"
    id           = db.Column(db.Integer, primary_key=True)
    doctor_id    = db.Column(db.String(30), unique=True, nullable=False)  # e.g. DR-001
    name         = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(80), default="General Physician")
    password_hash = db.Column(db.String(256), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    consultations = db.relationship("Consultation", backref="doctor", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "doctor_id": self.doctor_id,
                "name": self.name, "specialization": self.specialization}


class Consultation(db.Model):
    __tablename__ = "consultations"
    id           = db.Column(db.Integer, primary_key=True)
    doctor_id    = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    patient_id   = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)
    chief_complaint = db.Column(db.Text)
    doctor_notes = db.Column(db.Text)
    status       = db.Column(db.String(20), default="Open")  # Open | Closed
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
