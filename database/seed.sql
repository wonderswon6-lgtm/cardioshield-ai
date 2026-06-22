-- seed.sql — Sample data for development/testing
-- (Patient and prediction tables are kept empty for clean clinical deployment. Model metrics are seeded here.)

INSERT INTO model_metrics (model_name,accuracy,precision,recall,f1_score,roc_auc,specificity)
VALUES
  ('logistic_regression',0.8525,0.8600,0.8700,0.8649,0.9120,0.8300),
  ('decision_tree',      0.8197,0.8250,0.8400,0.8324,0.8700,0.8000),
  ('random_forest',      0.8852,0.8900,0.8980,0.8940,0.9350,0.8700),
  ('neural_network',     0.8770,0.8820,0.8850,0.8835,0.9280,0.8600);

