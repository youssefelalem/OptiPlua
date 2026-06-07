"""
OptiPlua ML Inference Module
Makes predictions using trained XGBoost model
"""

import logging
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from models.feature_engineering import preprocess_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptiPluaPredictor:
    """Inference wrapper for OptiPlua ML model"""

    def __init__(self, model_dir: str = 'models'):
        """Load trained model and artifacts"""
        self.model_dir = Path(model_dir)

        logger.info(f"Loading model from {self.model_dir}/optiplua_model.pkl...")
        self.model = joblib.load(self.model_dir / 'optiplua_model.pkl')
        self.feature_names = joblib.load(self.model_dir / 'feature_names.pkl')

        logger.info("✅ Model loaded successfully!")
        logger.info(f"   - Features: {len(self.feature_names)}")
        logger.info(f"   - Model type: {type(self.model).__name__}")

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features using the SAME pipeline as training.

        Delegates to ``models.feature_engineering.preprocess_data`` so that
        inference produces exactly the columns (and uses the same fitted
        scaler/encoders) the model was trained on.
        """
        X, _, _ = preprocess_data(df, is_training=False)
        # Guarantee column order matches what the model was fitted on.
        X = X.reindex(columns=self.feature_names)
        return X

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Make predictions on dataframe"""
        X = self.prepare_features(df)
        predictions = self.model.predict(X)
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
        'Type_Etablissement': ['Universite'],
        'Niveau': ['Licence_1'],
        'Nom_Matiere': ['ANALYSE'],
        'Type_Salle': ['Generale'],
        'Nb_Etudiants': [45],
        'Capacite_Salle': [60],
        'Nb_Tentatives': [1],
        'Heure_Debut': ['08:00'],
        'Heure_Fin': ['10:00'],
        'Jour': ['Lundi'],
        'ID_Enseignant': ['ENS_001'],
        'ID_Salle': ['SALLE_001'],
    })
    
    pred = predictor.predict(sample_schedule)[0]
    
    print(f"\nSample Schedule:")
    print(f"  {sample_schedule['Nb_Etudiants'][0]} students → {sample_schedule['Capacite_Salle'][0]}-seat room")
    print(f"  {sample_schedule['Type_Etablissement'][0]}, {sample_schedule['Niveau'][0]}, {sample_schedule['Jour'][0]} {sample_schedule['Heure_Debut'][0]}")
    print(f"\n  🎯 Predicted Quality Score: {pred:.2f}/100")
    
    print("\n✅ Inference demo complete!\n")


if __name__ == '__main__':
    demo()
