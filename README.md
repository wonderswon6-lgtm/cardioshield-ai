# CardioShield AI

> AI-powered Heart Disease Prediction Web Application  
> Built with Python · Flask · PostgreSQL · scikit-learn · Bootstrap

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 15+ running locally (password: `saanu0216`)

### 2. Create PostgreSQL Database
```sql
psql -U postgres -c "CREATE DATABASE cardioshield_db;"
psql -U postgres -d cardioshield_db -f database/schema.sql
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
- Clean the dataset (`dataset/raw/heart.csv`)
- Train Logistic Regression, Decision Tree, Random Forest, Neural Network (MLP)
- Perform GridSearchCV hyperparameter tuning
- Save models to `saved_models/`
- Generate charts to `reports/` and copy to `static/images/`

### 5. Start the Flask Server
```bash
python run.py
```
Open **http://127.0.0.1:5000**

---

## 📁 Project Structure

```
cardioshield-ai/
├── dataset/
│   ├── raw/heart.csv            ← Original UCI dataset
│   └── processed/               ← Cleaned + split CSVs
├── src/
│   ├── data/                    ← data_loader, data_cleaning, preprocessing
│   └── train_models.py          ← Full training pipeline
├── saved_models/                ← Trained .pkl files
├── reports/                     ← PNG charts (confusion matrices, ROC, etc.)
├── app/
│   ├── backend/
│   │   ├── app.py               ← Flask factory
│   │   ├── config.py            ← Config / DB credentials
│   │   ├── routes/routes.py     ← All API + page routes
│   │   ├── services/            ← prediction_service, db_service
│   │   └── database/models.py   ← SQLAlchemy ORM
│   └── frontend/
│       ├── templates/           ← Jinja2 HTML templates
│       └── static/              ← CSS, JS, images
├── database/schema.sql          ← PostgreSQL schema
├── deployment/.env              ← Credentials
├── tests/                       ← pytest unit tests
├── main.py                      ← Train + serve
└── run.py                       ← Server only
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict` | Run heart disease prediction |
| GET | `/api/models` | List available models |
| GET | `/api/analytics/stats` | Prediction statistics |
| GET | `/api/analytics/recent` | Recent 50 predictions |
| GET | `/api/analytics/metrics` | Model performance metrics |
| GET | `/api/patients` | All patient records |
| POST | `/api/train` | Trigger training (background) |
| GET | `/health` | Health check |

### Prediction Request Example
```json
POST /api/predict
{
  "age": 63, "sex": 1, "cp": 3, "trestbps": 145, "chol": 233,
  "fbs": 1, "restecg": 0, "thalach": 150, "exang": 0,
  "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1,
  "model": "random_forest",
  "name": "John Doe"
}
```

### Response
```json
{
  "status": "success",
  "prediction": 1,
  "probability": 84.2,
  "confidence": 91.3,
  "risk_level": "High",
  "recommendation": "High cardiovascular risk detected. Seek immediate medical evaluation.",
  "model_used": "random_forest",
  "patient_id": 1,
  "prediction_id": 1
}
```

---

## 🤖 ML Models

| Model | Accuracy | ROC AUC |
|-------|----------|---------|
| Logistic Regression | 85.2% | 91.2% |
| Decision Tree | 82.0% | 87.0% |
| **Random Forest** | **88.5%** | **93.5%** |
| Neural Network (MLP) | 87.7% | 92.8% |

All models tuned via **GridSearchCV** with 5-fold stratified cross-validation.

---

## 🛢️ Database

PostgreSQL with 3 tables:
- **patients** — clinical input data
- **predictions** — model outputs + risk level
- **model_metrics** — performance tracking

Credentials: `postgres` / `saanu0216` / DB: `cardioshield_db`

---

## 🧪 Running Tests
```bash
pytest tests/ -v
```
