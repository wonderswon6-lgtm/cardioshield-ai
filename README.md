# CardioShield AI

> **AI-Powered Heart Disease Prediction & Clinical Decision Support System**  
> A multi-role web platform for Doctors, Data Scientists, and Health Insurance Providers  
> Built with Python · Flask · PostgreSQL · scikit-learn · Bootstrap · Chart.js

---

## 🏥 Overview

CardioShield AI is a full-stack heart disease prediction system powered by a 4-model ML ensemble. The platform is designed for **three distinct user categories**, each with its own isolated portal and workflow:

| Portal | Target User | Access URL |
|--------|-------------|------------|
| 🩺 **CDSS** | Doctors & Clinicians | `/cdss/login` |
| 📊 **Data Analytics** | Data Scientists & Researchers | `/dashboard` |
| 🛡️ **Insurance Risk** | Health Insurance Underwriters | `/insurance-dashboard` |

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 15+ running locally

### 2. Create PostgreSQL Database
```sql
psql -U postgres -c "CREATE DATABASE cardioshield_db;"
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Train Models (first time only)
```bash
python main.py --train
```
This will:
- Load and clean the UCI Heart Disease dataset (`dataset/raw/heart.csv`)
- Train **4 ML models**: Logistic Regression, Decision Tree, Random Forest, Neural Network (MLP)
- Perform GridSearchCV hyperparameter tuning with 5-fold stratified cross-validation
- Save trained models to `saved_models/`
- Generate performance charts to `reports/` and copy to `static/images/`

### 5. Start the Server
```bash
python run.py
```
Open **http://127.0.0.1:5000**

---

## 📁 Project Structure

```
cardioshield-ai/
├── dataset/
│   ├── raw/heart.csv                    ← UCI Heart Disease dataset (303 samples, 14 features)
│   └── processed/                       ← Cleaned + train/test split CSVs
├── src/
│   ├── data/                            ← data_loader, data_cleaning, preprocessing
│   └── train_models.py                  ← Full training pipeline
├── saved_models/                        ← Trained .pkl files (4 models)
├── reports/                             ← PNG charts (confusion matrices, ROC curves, feature importance)
├── notebooks/                           ← Jupyter notebooks for EDA
├── app/
│   ├── backend/
│   │   ├── app.py                       ← Flask application factory
│   │   ├── config.py                    ← DB credentials & app config
│   │   ├── routes/
│   │   │   ├── routes.py                ← Main API & page routes
│   │   │   └── cdss_routes.py           ← CDSS Blueprint (/cdss/*)
│   │   ├── services/
│   │   │   ├── prediction_service.py    ← Model loading & inference
│   │   │   ├── db_service.py            ← Patient & prediction CRUD
│   │   │   ├── cdss_service.py          ← Doctor auth & consultation logic
│   │   │   ├── insurance_service.py     ← Insurance risk scoring
│   │   │   ├── explanation_service.py   ← Perturbation-based feature importance
│   │   │   └── evaluation_service.py   ← Model metrics evaluation
│   │   └── database/
│   │       └── models.py                ← SQLAlchemy ORM (Patient, Prediction, Doctor, Consultation, ModelMetric)
│   └── frontend/
│       ├── templates/
│       │   ├── home.html                ← 3-portal landing page
│       │   ├── prediction.html          ← Data Scientist prediction form
│       │   ├── result.html              ← Prediction results page
│       │   ├── dashboard.html           ← Analytics dashboard
│       │   ├── insurance_dashboard.html ← Insurance risk dashboard
│       │   └── cdss/
│       │       ├── login.html           ← Doctor login
│       │       ├── patient_search.html  ← Patient search
│       │       ├── new_patient.html     ← Full clinical intake form
│       │       └── consultation.html    ← AI consultation page
│       └── static/
│           ├── css/style.css
│           ├── js/script.js
│           └── images/                  ← Chart PNGs
├── database/schema.sql                  ← PostgreSQL schema
├── deployment/.env                      ← Environment credentials
├── tests/                               ← pytest unit tests
├── main.py                              ← Train + serve entry point
└── run.py                               ← Server-only entry point
```

---

## 🧭 User Portals

### 🩺 Portal 1 — Clinical Decision Support System (CDSS)

Designed to feel like real hospital software. Doctors log in with their credentials and never interact with external tools.

**Workflow:**
```
Doctor Login → Patient Search → New Patient Intake → AI Consultation → Save Report
```

**Key Pages:**

| Page | Route | Description |
|------|-------|-------------|
| Login | `/cdss/login` | Doctor ID + password authentication |
| Patient Search | `/cdss/patients` | Search existing patients by name or ID |
| New Patient Intake | `/cdss/new_patient` | Full 13-feature clinical form with sliders + doctor-friendly labels |
| Consultation | `/cdss/consult/<id>` | AI prediction with risk meter, consensus banner, risk/protective factors, recommendations |

**CDSS Features:**
- Full clinical intake form with sliders (Age, BP, Cholesterol, HR, Oldpeak, CA) and categorical dropdowns
- Real-time clinical alert badges (e.g., "High BP", "Borderline Cholesterol")
- On submission: registers patient, runs all 4 models, saves predictions, opens consultation immediately
- Consultation page shows:
  - **Overall cardiac risk score** with visual meter
  - **AI consensus banner** — e.g. *"⚠️ All 4 models agree — high cardiac risk"*
  - **Risk factors** (what is driving up the risk)
  - **Protective factors** (what is lowering risk)
  - **Clinical recommendations** (urgent/moderate/informational)
  - **Doctor notes** with report save functionality
- No model names or technical ML output shown — designed for clinical decision-making

---

### 📊 Portal 2 — Data Analytics Dashboard

For ML engineers and health researchers who want full access to model behaviour and data.

**Key Pages:**

| Page | Route | Description |
|------|-------|-------------|
| Prediction Form | `/predict` | 13-feature form with sliders for quick prediction |
| Results | `/result` | Per-model comparison, risk gauge, risk/protective factor analysis |
| Dashboard | `/dashboard` | KPI cards, prediction history, model performance metrics, charts |

**Dashboard Features:**
- KPI cards: Total predictions, Disease rate, Risk distribution
- Recent predictions table with edit/delete, bulk operations, outcome tracking
- ROC curves and feature importance charts
- Model performance metrics (Accuracy, F1, ROC-AUC)

---

### 🛡️ Portal 3 — Insurance Risk Assessment

For health insurance underwriters assessing cardiac risk for applicants.

**Key Pages:**

| Page | Route | Description |
|------|-------|-------------|
| Insurance Dashboard | `/insurance-dashboard` | Full applicant risk registry and underwriting decisions |

**Dashboard Features:**
- KPI cards: Total Assessments, Low / Medium / High Risk applicants
- Risk Distribution doughnut chart
- Per-applicant risk gauge, clinical risk factor table (ML-derived)
- Underwriting recommendation: Risk Category, Premium level, Suggested action
- Searchable applicant registry table

---

## 🔌 API Endpoints

### Main Application APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict` | Run prediction with all 4 models |
| GET | `/api/models` | List available trained models |
| GET | `/api/analytics/stats` | Prediction statistics summary |
| GET | `/api/analytics/recent` | Recent 50 predictions |
| GET | `/api/analytics/metrics` | Model performance metrics |
| GET | `/api/patient/<id>/predictions` | All predictions for a patient |
| PUT | `/api/prediction/<id>` | Update prediction metadata |
| DELETE | `/api/prediction/<id>` | Delete a prediction |
| DELETE | `/api/predictions/bulk` | Bulk delete predictions |
| POST | `/api/patient/<id>/outcome` | Set actual clinical outcome |
| GET | `/health` | Health check |

### CDSS APIs (`/cdss/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/cdss/login` | Doctor authentication |
| GET | `/cdss/logout` | Clear session |
| GET | `/cdss/patients` | Patient search |
| GET/POST | `/cdss/new_patient` | New patient intake form & submission |
| GET | `/cdss/consult/<id>` | Open consultation for a patient |
| POST | `/cdss/api/predict` | Run ensemble prediction (CDSS context) |
| POST | `/cdss/api/consultation/<id>/save` | Save doctor notes & report |
| GET | `/cdss/api/patients/search` | JSON patient autocomplete |

### Insurance APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/insurance/patient/<id>/risk-factors` | ML-derived risk factor breakdown |

---

### Prediction Request Example
```json
POST /api/predict
{
  "age": 63, "sex": 1, "cp": 3, "trestbps": 145, "chol": 233,
  "fbs": 1, "restecg": 0, "thalach": 150, "exang": 0,
  "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1,
  "name": "John Doe"
}
```

### Response
```json
{
  "status": "success",
  "predictions": [
    {
      "model_used": "random_forest",
      "prediction": 1,
      "probability": 84.2,
      "confidence": 91.3,
      "risk_level": "High",
      "recommendation": "High cardiovascular risk. Immediate cardiology referral advised.",
      "feature_contributions": [...]
    }
  ],
  "patient_id": 42,
  "patient_name": "John Doe"
}
```

---

## 🤖 ML Models

All 4 models are trained on the [UCI Heart Disease Dataset](https://archive.ics.uci.edu/dataset/45/heart+disease) (303 samples, 13 features, binary classification).

| Model | Accuracy | ROC AUC |
|-------|----------|---------|
| Logistic Regression | ~85% | ~91% |
| Decision Tree | ~82% | ~87% |
| **Random Forest** | **~88%** | **~93%** |
| Neural Network (MLP) | ~87% | ~92% |

- Tuned via **GridSearchCV** with 5-fold stratified cross-validation
- **Feature importance** computed via perturbation-based explanation (`explanation_service.py`)
- **Ensemble prediction** = average probability across all 4 models

### Input Features

| Feature | Description | Range |
|---------|-------------|-------|
| `age` | Age in years | 1–100 |
| `sex` | Sex (1=Male, 0=Female) | 0–1 |
| `cp` | Chest pain type | 0–3 |
| `trestbps` | Resting blood pressure (mmHg) | 80–200 |
| `chol` | Serum cholesterol (mg/dL) | 100–600 |
| `fbs` | Fasting blood sugar > 120 mg/dL | 0–1 |
| `restecg` | Resting ECG results | 0–2 |
| `thalach` | Maximum heart rate achieved (bpm) | 60–220 |
| `exang` | Exercise-induced angina | 0–1 |
| `oldpeak` | ST depression (mm) | 0–6.2 |
| `slope` | Slope of peak exercise ST segment | 0–2 |
| `ca` | Number of major vessels (fluoroscopy) | 0–3 |
| `thal` | Thalassemia type | 1–3 |

---

## 🛢️ Database

PostgreSQL with 5 tables:

| Table | Description |
|-------|-------------|
| `patients` | Clinical input data for each patient |
| `predictions` | ML model outputs, risk level, recommendation |
| `doctors` | CDSS doctor accounts |
| `consultations` | CDSS consultation sessions with notes |
| `model_metrics` | Model performance tracking over time |

**Default credentials:**  
Host: `localhost` · Port: `5432` · DB: `cardioshield_db` · User: `postgres`

---

## 🔐 Authentication

- **CDSS Portal**: Session-based login with `doctor_id` + password. All CDSS routes are protected by `@doctor_required` decorator.
- **Default demo doctor**: seeded automatically on first login attempt.
  - Doctor ID: `DOC001`
  - Password: `doctor123`
- Sessions use `SESSION_COOKIE_HTTPONLY` for security.

---

## 🧪 Running Tests
```bash
pytest tests/ -v
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.x |
| ORM | SQLAlchemy |
| Database | PostgreSQL 15 |
| ML | scikit-learn, NumPy, pandas, joblib |
| Frontend | HTML5, CSS3 (Vanilla), Bootstrap 5.3, Chart.js 4 |
| Fonts | Google Fonts — Inter |
| Deployment | Gunicorn (via Procfile) |

---

## 📋 Environment Variables

Set in `deployment/.env`:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/cardioshield_db
SECRET_KEY=your_secret_key
FLASK_ENV=development
```

---

## 📄 License

This project was built as part of an academic capstone project. Dataset sourced from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/45/heart+disease).
