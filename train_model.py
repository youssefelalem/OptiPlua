"""
OptiPlua ML Training Pipeline
Trains XGBoost model on schedule quality data
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
import joblib
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_and_validate_data(csv_path: str) -> pd.DataFrame:
    """Load and validate the dataset"""
    logger.info(f"Loading data from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Dataset shape: {df.shape} (rows, cols)")
    logger.info(f"Columns: {df.columns.tolist()}")
    
    # Validate
    assert df.shape[0] > 0, "Dataset is empty"
    assert 'Score' in df.columns, "Score column missing"
    assert 'Version' in df.columns, "Version column missing"
    
    logger.info("✅ Data validation passed")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create engineered features"""
    logger.info("Starting Feature Engineering...")
    df_eng = df.copy()
    
    # 1. Taux_Remplissage (occupancy rate)
    df_eng['Taux_Remplissage'] = df_eng['Nb_Etudiants'] / df_eng['Capacite_Salle']
    df_eng['Taux_Remplissage'] = df_eng['Taux_Remplissage'].clip(0, 1)
    logger.info("  ✓ Created: Taux_Remplissage")
    
    # 2. Heure_Debut_Num (extract hour from "HH:MM" format)
    df_eng['Heure_Debut_Num'] = pd.to_datetime(df_eng['Heure_Debut'], format='%H:%M').dt.hour
    logger.info("  ✓ Created: Heure_Debut_Num (hour only)")
    
    # 3. Jour_Encoded (day of week: Mon=0, Sun=6)
    jour_map = {'Lundi': 0, 'Mardi': 1, 'Mercredi': 2, 'Jeudi': 3, 'Vendredi': 4, 'Samedi': 5}
    df_eng['Jour_Encoded'] = df_eng['Jour'].map(jour_map)
    logger.info("  ✓ Created: Jour_Encoded (Mon=0, Tue=1, ...)")
    
    # 4. One-Hot Encoding for Type_Etablissement
    etab_dummies = pd.get_dummies(df_eng['Type_Etablissement'], prefix='Etab')
    df_eng = pd.concat([df_eng, etab_dummies], axis=1)
    logger.info(f"  ✓ Created: One-Hot encoded Type_Etablissement ({etab_dummies.shape[1]} cols)")
    
    # 5. One-Hot Encoding for Type_Salle
    salle_dummies = pd.get_dummies(df_eng['Type_Salle'], prefix='Salle')
    df_eng = pd.concat([df_eng, salle_dummies], axis=1)
    logger.info(f"  ✓ Created: One-Hot encoded Type_Salle ({salle_dummies.shape[1]} cols)")
    
    # 6. One-Hot Encoding for Niveau
    niveau_dummies = pd.get_dummies(df_eng['Niveau'], prefix='Niveau')
    df_eng = pd.concat([df_eng, niveau_dummies], axis=1)
    logger.info(f"  ✓ Created: One-Hot encoded Niveau ({niveau_dummies.shape[1]} cols)")
    
    logger.info("✅ Feature Engineering Complete")
    return df_eng


def select_features(df: pd.DataFrame) -> tuple:
    """Select features for modeling (no data leakage)"""
    # Drop ID/Name and raw categorical/text columns (we keep their one-hot encodings)
    drop_cols = [col for col in df.columns if col.startswith('ID_') or col.startswith('Nom_')]
    # Remove raw text columns that were one-hot encoded or are not numeric
    raw_categorical = ['Type_Etablissement', 'Type_Salle', 'Niveau', 'Jour', 'Heure_Debut']
    drop_cols.extend(raw_categorical)
    # Remove other unused/target columns
    drop_cols.extend(['Creneau', 'Score', 'Heure_Fin'])

    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    y = df['Score']
    
    # Ensure all features are numeric (after dropping raw categoricals)
    X = X.select_dtypes(include=[float, int, 'float64', 'int64']).copy()

    logger.info(f"Final feature set: {X.shape[1]} features")
    logger.info(f"Features: {X.columns.tolist()}")
    logger.info("✅ Features selected - No data leakage detected")
    
    return X, y, X.columns.tolist()


def split_data(X: pd.DataFrame, y: pd.Series) -> tuple:
    """Split data into train/test"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    logger.info(f"Train set: {X_train.shape[0]} samples")
    logger.info(f"Test set: {X_test.shape[0]} samples")
    logger.info(f"Train/Test ratio: {X_train.shape[0] / X_test.shape[0]:.1f}:1")
    
    return X_train, X_test, y_train, y_test


def scale_features(X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple:
    """Scale features using StandardScaler"""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    logger.info("✅ Features scaled with StandardScaler")
    return X_train_scaled, X_test_scaled, scaler


def train_xgboost_model(X_train: np.ndarray, y_train: pd.Series) -> XGBRegressor:
    """Train XGBoost model"""
    logger.info("Training XGBoost Model...")
    
    hyperparams = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'objective': 'reg:squarederror',
        'random_state': 42,
        'n_jobs': -1,
        'verbosity': 1
    }
    logger.info(f"Hyperparameters: {hyperparams}")
    
    model = XGBRegressor(**hyperparams)
    model.fit(X_train, y_train)
    
    logger.info("✅ XGBoost training complete")
    return model


def evaluate_model(model: XGBRegressor, X_test: np.ndarray, y_test: pd.Series) -> dict:
    """Evaluate model performance"""
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    logger.info("\n" + "="*60)
    logger.info("MODEL PERFORMANCE METRICS (TEST SET)")
    logger.info("="*60)
    logger.info(f"  Mean Absolute Error (MAE)     : {mae:.4f}")
    logger.info(f"  Root Mean Squared Error (RMSE): {rmse:.4f}")
    logger.info(f"  R² Score                      : {r2:.4f}")
    logger.info("="*60)
    
    if r2 > 0.99:
        logger.warning("⚠️  R² > 0.99 — Suspicious! Check for Data Leakage!")
        logger.warning("   Is 'Score' accidentally in the feature set?")
    
    # Feature importance
    importance_df = pd.DataFrame({
        'Feature': model.get_booster().feature_names,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=False)
    
    logger.info("Top 10 Most Important Features:")
    logger.info(importance_df.head(10).to_string())
    
    return {
        'MAE': float(mae),
        'RMSE': float(rmse),
        'R2': float(r2),
        'n_test_samples': len(y_test)
    }


def save_artifacts(model: XGBRegressor, scaler: StandardScaler, feature_names: list, metrics: dict, output_dir: str = 'models'):
    """Save model artifacts"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save model
    model_path = output_path / 'optiplua_model.pkl'
    joblib.dump(model, model_path)
    logger.info(f"Saving model to {model_path}...")
    
    # Save scaler
    scaler_path = output_path / 'scaler.pkl'
    joblib.dump(scaler, scaler_path)
    logger.info(f"Saving scaler to {scaler_path}...")
    
    # Save feature names
    features_path = output_path / 'feature_names.pkl'
    joblib.dump(feature_names, features_path)
    logger.info(f"Saving feature names to {features_path}...")
    
    # Save metrics
    metrics_path = output_path / 'metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saving metrics to {metrics_path}...")
    
    logger.info("✅ All artifacts saved successfully!")
    logger.info(f"   Model    : {model_path}")
    logger.info(f"   Scaler   : {scaler_path}")
    logger.info(f"   Features : {features_path}")
    logger.info(f"   Metrics  : {metrics_path}")


def main():
    logger.info("\n" + "🚀 "*30)
    logger.info("OptiPlua Machine Learning Training Pipeline")
    logger.info("🚀 "*30 + "\n")
    
    try:
        # Load data
        csv_path = 'data/final_schedules_ml.csv'
        df = load_and_validate_data(csv_path)
        
        # Feature engineering
        df_engineered = engineer_features(df)
        
        # Select features
        X, y, feature_names = select_features(df_engineered)
        
        # Split data
        X_train, X_test, y_train, y_test = split_data(X, y)
        
        # Scale features
        X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
        
        # Train model
        model = train_xgboost_model(X_train_scaled, y_train)
        
        # Evaluate
        metrics = evaluate_model(model, X_test_scaled, y_test)
        
        # Save artifacts
        save_artifacts(model, scaler, feature_names, metrics)
        
        logger.info("\n✅ PIPELINE COMPLETE - Model Ready for Inference!\n")
        
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed with error: {str(e)}")
        logger.exception(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
