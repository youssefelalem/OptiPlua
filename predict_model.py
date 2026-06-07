"""
OptiPlua ML Inference Module
Makes predictions using trained XGBoost model
"""

import logging
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from typing import Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptiPluaPredictor:
    """Inference wrapper for OptiPlua ML model"""
    
    def __init__(self, model_dir: str = 'models'):
        """Load trained model and artifacts"""
        self.model_dir = Path(model_dir)
        
        logger.info(f"Loading model from {self.model_dir}/optiplua_model.pkl...")
        self.model = joblib.load(self.model_dir / 'optiplua_model.pkl')
        self.scaler = joblib.load(self.model_dir / 'scaler.pkl')
        self.feature_names = joblib.load(self.model_dir / 'feature_names.pkl')
        
        logger.info("✅ Model loaded successfully!")
        logger.info(f"   - Features: {len(self.feature_names)}")
        logger.info(f"   - Model type: {type(self.model).__name__}")
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply same feature engineering as training"""
        df_eng = df.copy()
        
        # Taux_Remplissage
        if 'Nb_Etudiants' in df_eng.columns and 'Capacite_Salle' in df_eng.columns:
            df_eng['Taux_Remplissage'] = df_eng['Nb_Etudiants'] / df_eng['Capacite_Salle']
            df_eng['Taux_Remplissage'] = df_eng['Taux_Remplissage'].clip(0, 1)
        
        # Heure_Debut_Num
        if 'Heure_Debut' in df_eng.columns:
            df_eng['Heure_Debut_Num'] = pd.to_datetime(df_eng['Heure_Debut'], format='%H:%M').dt.hour
        
        # Jour_Encoded
        if 'Jour' in df_eng.columns:
            jour_map = {'Lundi': 0, 'Mardi': 1, 'Mercredi': 2, 'Jeudi': 3, 'Vendredi': 4, 'Samedi': 5}
            df_eng['Jour_Encoded'] = df_eng['Jour'].map(jour_map)
        
        # One-Hot Encoding
        for col, prefix in [('Type_Etablissement', 'Etab'), ('Type_Salle', 'Salle'), ('Niveau', 'Niveau')]:
            if col in df_eng.columns:
                dummies = pd.get_dummies(df_eng[col], prefix=prefix)
                df_eng = pd.concat([df_eng, dummies], axis=1)
        
        return df_eng
    
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for prediction"""
        df_eng = self.engineer_features(df)

        for feat in self.feature_names:
            if feat not in df_eng.columns:
                logger.warning(f"Feature '{feat}' missing, filling with 0")
                df_eng[feat] = 0

        X = df_eng[self.feature_names].copy()
        X_scaled = self.scaler.transform(X)
        return X_scaled
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Make predictions on dataframe"""
        X_scaled = self.prepare_features(df)
        predictions = self.model.predict(X_scaled)
        predictions = np.clip(predictions, 0, 100)  # Scores should be 0-100
        return predictions
    
    def predict_batch(self, csv_path: str, output_path: str = None) -> pd.DataFrame:
        """Predict on CSV file"""
        df = pd.read_csv(csv_path)
        predictions = self.predict(df)
        
        result = df.copy()
        result['Predicted_Score'] = predictions
        
        if output_path:
            result.to_csv(output_path, index=False)
            logger.info(f"Predictions saved to {output_path}")
        
        return result


def demo():
    """Demo inference scenarios"""
    print("\n🎓 OptiPlua — Model Inference Demo\n")
    
    predictor = OptiPluaPredictor()
    
    # Demo 1: Batch prediction
    print("="*60)
    print("DEMO 1: Predicting on raw_schedules_test.csv")
    print("="*60)
    
    try:
        df_raw = pd.read_csv('data/raw_schedules_test.csv')
        predictions = predictor.predict(df_raw)
        
        print(f"\nPredictions (first 10 samples):")
        print(f"  Min score:  {predictions.min():.2f}")
        print(f"  Max score:  {predictions.max():.2f}")
        print(f"  Mean score: {predictions.mean():.2f}")
        print(f"  Std dev:    {predictions.std():.2f}")
    except Exception as e:
        print(f"⚠️  Error: {e}")
    
    # Demo 2: Single schedule prediction
    print("\n" + "="*60)
    print("DEMO 2: Creating and scoring a single schedule")
    print("="*60)
    
    sample_schedule = pd.DataFrame({
        'Niveau': ['Licence_1'],
        'Nb_Etudiants': [45],
        'Capacite_Salle': [60],
        'Heure_Debut': ['08:00'],
        'Jour': ['Lundi'],
        'Type_Etablissement': ['Universite'],
        'Type_Salle': ['Generale'],
        'Version': [0]
    })
    
    pred = predictor.predict(sample_schedule)[0]
    
    print(f"\nSample Schedule:")
    print(f"  {sample_schedule['Nb_Etudiants'][0]} students → {sample_schedule['Capacite_Salle'][0]}-seat room")
    print(f"  {sample_schedule['Type_Etablissement'][0]}, {sample_schedule['Niveau'][0]}, {sample_schedule['Jour'][0]} {sample_schedule['Heure_Debut'][0]}")
    print(f"\n  🎯 Predicted Quality Score: {pred:.2f}/100")
    
    print("\n✅ Inference demo complete!\n")


if __name__ == '__main__':
    demo()
