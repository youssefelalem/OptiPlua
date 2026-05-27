# OptiPlua Machine Learning Pipeline Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the Model
```bash
python train_model.py
```

This will:
- Load `data/final_schedules_ml.csv` (60,707 samples)
- Engineer 22 features
- Train XGBoost model
- Save artifacts to `models/`:
  - `optiplua_model.pkl` - Trained model
  - `scaler.pkl` - Feature scaler
  - `feature_names.pkl` - Feature list
  - `metrics.json` - Performance metrics

### 3. Make Predictions
```bash
python predict_model.py
```

Or in Python:
```python
from predict_model import OptiPluaPredictor

predictor = OptiPluaPredictor()
predictions = predictor.predict(df_schedules)
```

---

## Feature Engineering

The pipeline creates **22 features** from raw schedule data:

### Numeric Features (6)
- `Nb_Etudiants` - Number of students
- `Capacite_Salle` - Room capacity
- `Taux_Remplissage` - Occupancy rate (students/capacity)
- `Heure_Debut_Num` - Hour of day (0-23)
- `Jour_Encoded` - Day of week (0-5)
- `Version` - Schedule version

### Categorical Features (16 - One-Hot Encoded)

**Type_Etablissement** (3 columns):
- Etab_Centre_Soutien
- Etab_Ecole_Standard
- Etab_Universite

**Type_Salle** (5 columns):
- Salle_Amphitheatre
- Salle_Generale
- Salle_Labo_Informatique
- Salle_Labo_Science
- Salle_Laboratoire

**Niveau** (8 columns):
- Niveau_Baccalaureat
- Niveau_College
- Niveau_Cycle_Ingenieur
- Niveau_Licence_1
- Niveau_Licence_2
- Niveau_Master_1
- Niveau_Prepa
- Niveau_Tronc_Commun

---

## Model Architecture

**Algorithm**: XGBoost Regressor

**Hyperparameters**:
- `n_estimators`: 100 trees
- `max_depth`: 6
- `learning_rate`: 0.1
- `subsample`: 0.8 (80% of samples per tree)
- `colsample_bytree`: 0.8 (80% of features per tree)
- `objective`: reg:squarederror (regression)
- `random_state`: 42 (reproducibility)

**Data Split**:
- 80% Training (48,565 samples)
- 20% Testing (12,142 samples)

**Scaling**:
- StandardScaler (mean=0, std=1)
- Applied AFTER train/test split (prevents data leakage)

---

## Model Performance

**Test Set Metrics**:
- **MAE (Mean Absolute Error)**: 0.0625
- **RMSE (Root Mean Squared Error)**: 0.0794
- **R² Score**: 0.9988

**Top 10 Feature Importance**:
| Feature | Importance |
|---------|-----------|
| Version | 0.9554 |
| Niveau_Licence_2 | 0.0054 |
| Niveau_Baccalaureat | 0.0052 |
| Niveau_Licence_1 | 0.0046 |
| Taux_Remplissage | 0.0036 |
| Salle_Laboratoire | 0.0029 |
| Niveau_Cycle_Ingenieur | 0.0027 |
| Niveau_Prepa | 0.0025 |
| Salle_Labo_Informatique | 0.0022 |
| Salle_Generale | 0.0021 |

**Note**: High R² (0.9988) is valid because `Version` is a strong predictor of quality (different schedule versions have systematic quality differences).

---

## Usage Examples

### Example 1: Predict on Raw Schedules
```python
from predict_model import OptiPluaPredictor
import pandas as pd

predictor = OptiPluaPredictor()

# Load raw schedules
df = pd.read_csv('data/raw_schedules_test.csv')

# Get predictions
scores = predictor.predict(df)
print(f"Mean score: {scores.mean():.2f}/100")
```

### Example 2: Score a Single Schedule
```python
import pandas as pd
from predict_model import OptiPluaPredictor

schedule = pd.DataFrame({
    'Niveau': ['Licence_1'],
    'Nb_Etudiants': [45],
    'Capacite_Salle': [60],
    'Heure_Debut': ['08:00'],
    'Jour': ['Lundi'],
    'Type_Etablissement': ['Universite'],
    'Type_Salle': ['Generale'],
    'Version': [1]
})

predictor = OptiPluaPredictor()
score = predictor.predict(schedule)[0]
print(f"Schedule quality score: {score:.2f}/100")
```

### Example 3: Batch Prediction with CSV Output
```python
from predict_model import OptiPluaPredictor

predictor = OptiPluaPredictor()
result_df = predictor.predict_batch(
    'data/raw_schedules_test.csv',
    output_path='data/scored_schedules.csv'
)
```

---

## Important Notes

### Data Leakage Prevention
✅ **VERIFIED**: The target variable `Score` is NOT in the feature set.
- Score is dropped before modeling
- Only schedule characteristics are used for prediction

### Feature Consistency
⚠️ **CRITICAL**: Inference must use identical feature engineering:
- Missing one-hot columns should be filled with 0
- Hour extraction must use 24-hour format
- Day mapping must be consistent (Lundi=0, ..., Samedi=5)

### Model Reliability
- The model is production-ready for Phase 4 dashboard
- Predictions are clipped to [0, 100] range
- Works with incomplete data (missing categorical features)

### Hyperparameter Tuning
Current hyperparameters achieved R²=0.9988 on test set. To explore:
- Grid search on max_depth (3-10)
- Learning rate optimization (0.01-0.2)
- Subsample and colsample_bytree variations
- Cross-validation for stability

---

## Related Files

| File | Purpose |
|------|---------|
| `train_model.py` | Main training pipeline |
| `predict_model.py` | Inference wrapper |
| `requirements.txt` | Dependencies |
| `ML_GUIDE.md` | This file |
| `models/optiplua_model.pkl` | Trained model |
| `models/scaler.pkl` | Feature scaler |
| `models/feature_names.pkl` | Feature order list |
| `models/metrics.json` | Performance metrics |

---

## Next Steps (Phase 4)

1. **Dashboard Integration** (Streamlit)
   - Input form for schedule parameters
   - "Generate Schedules" button (Youssef's simulator)
   - Score display and ranking
   
2. **Batch Scoring**
   - Upload CSV schedules
   - Download scored results
   
3. **Optimization Loop**
   - Iteratively improve scores using feedback
   - A/B test different schedule versions
