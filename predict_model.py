"""
OptiPlua ML Inference Module.

Predicts ONE quality score for a whole timetable. The input DataFrame (all the
session rows of a single timetable) is aggregated with the same
`aggregate_timetable` used at training time, then fed to the XGBoost model.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

from models.feature_engineering import features_for_timetable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptiPluaPredictor:
    """Inference wrapper for the OptiPlua timetable-quality model."""

    def __init__(self, model_dir: str = 'models'):
        self.model_dir = Path(model_dir)

        logger.info(f"Loading model from {self.model_dir}/optiplua_model.pkl...")
        self.model = joblib.load(self.model_dir / 'optiplua_model.pkl')
        self.feature_names = joblib.load(self.model_dir / 'feature_names.pkl')

        logger.info("Model loaded successfully.")
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
        """Predict the quality score (0-100) of one timetable.

        Returns a length-1 array so existing callers (e.g. ``np.mean(...)``)
        keep working.
        """
        X = self.prepare_features(df)
        pred = self.model.predict(X)
        return np.clip(pred, 0, 100)

    def predict_batch(self, csv_path: str, output_path: str = None) -> pd.DataFrame:
        """Score each timetable in a CSV (one row per ``Version``)."""
        df = pd.read_csv(csv_path)
        if 'Version' in df.columns:
            rows = [
                {'Version': ver, 'Predicted_Score': float(self.predict(grp)[0])}
                for ver, grp in df.groupby('Version')
            ]
            result = pd.DataFrame(rows)
        else:
            result = pd.DataFrame([{'Predicted_Score': float(self.predict(df)[0])}])

        if output_path:
            result.to_csv(output_path, index=False)
            logger.info(f"Predictions saved to {output_path}")
        return result


def demo():
    """Demo inference on the generated timetables."""
    print("\nOptiPlua - Model Inference Demo\n")

    predictor = OptiPluaPredictor()

    print("=" * 60)
    print("DEMO: Scoring timetables in raw_schedules_test.csv")
    print("=" * 60)
    try:
        result = predictor.predict_batch('data/raw_schedules_test.csv')
        print(f"\nScored {len(result)} timetable(s):")
        print(result.to_string(index=False))
        if 'Predicted_Score' in result.columns and len(result) > 1:
            s = result['Predicted_Score']
            print(f"\n  Range: {s.min():.2f} - {s.max():.2f}  |  Std: {s.std():.2f}")
    except Exception as e:
        print(f"Error: {e}")

    print("\nInference demo complete.\n")


if __name__ == '__main__':
    demo()
