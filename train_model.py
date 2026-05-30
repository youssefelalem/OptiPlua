
import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import json
import logging
from models.feature_engineering import preprocess_data

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_optiplua_model(data_path, model_output='models/optiplua_model.pkl'):
    logger.info(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Feature Engineering
    X, y, weights = preprocess_data(df, is_training=True)
    
    # Split
    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
        X, y, weights, test_size=0.2, random_state=42
    )
    
    # XGBoost Pipeline
    model = xgb.XGBRegressor(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='reg:squarederror',
        n_jobs=-1,
        random_state=42
    )
    
    logger.info("Fitting XGBoost model with sample weights...")
    model.fit(X_train, y_train, sample_weight=w_train)
    
    # Evaluation
    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    
    metrics = {
        "mse": float(mse),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2)
    }
    
    logger.info(f"Training Complete. Metrics: {metrics}")
    
    # Save artifacts
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, model_output)
    with open('models/metrics.json', 'w') as f:
        json.dump(metrics, f)
    
    # Save feature names for inference consistency
    joblib.dump(X.columns.tolist(), 'models/feature_names.pkl')
    
    return model

if __name__ == "__main__":
    # Check if bootstrap data exists, else use raw test data
    data_file = 'data/bootstrap_schedules.csv'
    if not os.path.exists(data_file):
        data_file = 'data/raw_schedules_test.csv'
        logger.warning(f"{data_file} not found. Using fallback.")
        
    train_optiplua_model(data_file)
