-- =============================================================================
-- CardioShield AI — PostgreSQL Schema
-- DB: cardioshield_db  |  User: postgres  |  Password: saanu0216
--
-- Run as:
--   psql -U postgres -c "CREATE DATABASE cardioshield_db;"
--   psql -U postgres -d cardioshield_db -f database/schema.sql
-- =============================================================================

CREATE TABLE IF NOT EXISTS patients (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(120),
    age         INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    sex         SMALLINT NOT NULL CHECK (sex IN (0,1)),
    cp          SMALLINT NOT NULL CHECK (cp BETWEEN 0 AND 3),
    trestbps    FLOAT NOT NULL,
    chol        FLOAT NOT NULL,
    fbs         SMALLINT NOT NULL CHECK (fbs IN (0,1)),
    restecg     SMALLINT NOT NULL CHECK (restecg BETWEEN 0 AND 2),
    thalach     FLOAT NOT NULL,
    exang       SMALLINT NOT NULL CHECK (exang IN (0,1)),
    oldpeak     FLOAT NOT NULL,
    slope       SMALLINT NOT NULL CHECK (slope BETWEEN 0 AND 2),
    ca          SMALLINT NOT NULL CHECK (ca BETWEEN 0 AND 4),
    thal        SMALLINT NOT NULL CHECK (thal BETWEEN 1 AND 3),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id              SERIAL PRIMARY KEY,
    patient_id      INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    model_used      VARCHAR(50) NOT NULL DEFAULT 'random_forest',
    prediction      SMALLINT NOT NULL CHECK (prediction IN (0,1)),
    probability     FLOAT NOT NULL,
    confidence      FLOAT NOT NULL,
    risk_level      VARCHAR(20) NOT NULL CHECK (risk_level IN ('Low','Moderate','High')),
    recommendation  TEXT,
    predicted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_metrics (
    id          SERIAL PRIMARY KEY,
    model_name  VARCHAR(50) NOT NULL,
    accuracy    FLOAT,
    precision   FLOAT,
    recall      FLOAT,
    f1_score    FLOAT,
    roc_auc     FLOAT,
    specificity FLOAT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pred_patient  ON predictions(patient_id);
CREATE INDEX IF NOT EXISTS idx_pred_at       ON predictions(predicted_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_name  ON model_metrics(model_name);
