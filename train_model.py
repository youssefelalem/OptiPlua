"""
OptiPlua — Train the timetable-quality XGBoost model.

Each training example is ONE timetable (rows grouped by `Version`), aggregated
into the TIMETABLE_FEATURES vector. This matches the granularity of the label
(a per-timetable score), unlike the previous per-session setup whose R2 was ~0.
"""

import os
import json
import logging

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

from models.feature_engineering import build_timetable_dataset, TIMETABLE_FEATURES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_optiplua_model(data_path, model_output='models/optiplua_model.pkl'):
    logger.info(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)

    logger.info("Aggregating sessions into timetable-level samples...")
    X, y = build_timetable_dataset(df)
    if y is None:
        raise ValueError("Training data must contain a 'Score' column.")
    logger.info(f"  {len(X)} timetables x {X.shape[1]} features")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Small, near-deterministic dataset -> shallow, regularised trees.
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective='reg:squarederror',
        n_jobs=-1,
        random_state=42,
    )

    logger.info("Fitting XGBoost (timetable-level)...")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    metrics = {
        "mse": float(mse),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2),
        "n_timetables": int(len(X)),
        "level": "timetable",
    }
    logger.info(f"Training complete. Metrics: {metrics}")

    os.makedirs('models', exist_ok=True)
    joblib.dump(model, model_output)
    joblib.dump(TIMETABLE_FEATURES, 'models/feature_names.pkl')
    with open('models/metrics.json', 'w') as f:
        json.dump(metrics, f)

    return model


if __name__ == "__main__":
    # Prefer the in-distribution, timetable-level dataset (same simulator +
    # heuristic as inference). Fall back to grouping the session-level bootstrap.
    candidates = ['data/ml_timetable_dataset.csv', 'data/bootstrap_schedules.csv']
    data_file = next((p for p in candidates if os.path.exists(p)), None)
    if data_file is None:
        raise FileNotFoundError(
            "No training data found. Run generate_ml_dataset.py first."
        )
    logger.info(f"Using training data: {data_file}")
    train_optiplua_model(data_file)
