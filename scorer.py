"""
OptiPlua — Scoring & Ranking des variantes d'emploi du temps.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple
from simulator import calculer_score_emploi


class TimetableScorer:

    def __init__(self, model_dir: str = 'models'):
        self._predictor = None
        self._model_dir = model_dir

    def _load_ml(self):
        if self._predictor is None:
            from predict_model import OptiPluaPredictor
            self._predictor = OptiPluaPredictor(model_dir=self._model_dir)

    def score_variant_ml(self, df_emploi: pd.DataFrame) -> float:
        self._load_ml()
        predictions = self._predictor.predict(df_emploi)
        return float(np.mean(predictions))

    def rank_variants(
        self,
        variants: List[Tuple[pd.DataFrame, float, dict]],
        method: str = 'heuristic',
    ) -> List[Tuple[pd.DataFrame, float, dict]]:
        if method == 'ml':
            self._load_ml()
            rescored = []
            for df_emp, _, details in variants:
                ml_score = self.score_variant_ml(df_emp)
                details = {**details, 'score_final': ml_score, 'methode': 'ml'}
                rescored.append((df_emp, ml_score, details))
            return sorted(rescored, key=lambda x: x[1], reverse=True)

        return sorted(variants, key=lambda x: x[1], reverse=True)
