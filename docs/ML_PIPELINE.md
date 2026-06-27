# OptiPlua — Machine Learning Pipeline

This document describes the **current** ML pipeline. It predicts a single quality
score (0–100) for a **whole timetable**.

> ℹ️ Earlier internal notes described a *per-session* model (22 one-hot features,
> a `StandardScaler`, `Version` as a predictor). That design is **obsolete** — it
> scored R² ≈ 0 and could not discriminate between variants. The pipeline below
> replaces it. See [Why timetable-level?](#why-timetable-level) for the rationale.

## Quick start

```bash
pip install -r requirements.txt

python generate_ml_dataset.py   # 1. build data/ml_timetable_dataset.csv (90 timetables)
python train_model.py           # 2. train & save models/optiplua_model.pkl
python predict_model.py         # 3. demo inference
```

## Why timetable-level?

The quality score describes a **whole** timetable, not a single session. Training
on individual session rows is unlearnable:

- ~182,000 session rows mapped to only **150** distinct scores (one per timetable);
- every row of a timetable shares the **same constant** score;
- per-row features (room, day, hour…) vary widely while the label does not.

Result: the model regresses to the global mean (**R² ≈ 0**), predictions collapse
to a ~0.1-wide band, and ranking is impossible.

**Fix:** aggregate each timetable's sessions into one feature vector and train one
example per timetable. Because training timetables come from the *same* simulator
and *same* heuristic used at inference time, there is no train/serve mismatch.

## Features (6, timetable-level)

Defined in [`models/feature_engineering.py`](../models/feature_engineering.py).
They deliberately mirror the four penalty terms of the heuristic score.

| Feature | Meaning |
|---|---|
| `teacher_gap_per_session` | teacher window-hours, per session |
| `class_gap_per_session` | student window-hours, per session |
| `overload_per_session` | (class, day) blocks with > 4 sessions, per session |
| `low_util_per_session` | rooms filled < 40%, per session |
| `avg_util` | mean room occupancy rate |
| `n_sessions` | timetable size |

## Target

The label is the heuristic score from `simulator.calculer_score_emploi`:

```
Score = 100 × (1 − total_penalty / (5 × n_sessions))
total_penalty = 2.0·teacher_gaps + 2.5·class_gaps
              + 1.0·daily_overloads + 1.5·under_filled_rooms
```

Across the 90 generated timetables the score ranges **15.96 → 96.69**
(σ ≈ 29.87) — a healthy, learnable spread.

## Model

XGBoost regressor, tuned for a small near-deterministic dataset:

| Hyperparameter | Value |
|---|---|
| `n_estimators` | 200 |
| `max_depth` | 3 |
| `learning_rate` | 0.05 |
| `subsample` | 0.9 |
| `colsample_bytree` | 0.9 |
| `objective` | `reg:squarederror` |

## Performance

| Metric | Value |
|---|---|
| R² (test) | **0.9996** |
| RMSE | **0.497** |
| Timetables | 90 (80/20 split) |

Feature importances (gain) are consistent with the score definition:
`teacher_gap_per_session` ≈ 0.80, `class_gap_per_session` ≈ 0.19, `avg_util` ≈ 0.01.

## Artifacts (`models/`)

| File | Purpose |
|---|---|
| `optiplua_model.pkl` | trained XGBoost model |
| `feature_names.pkl` | feature order (the 6 features above) |
| `metrics.json` | evaluation metrics |

## Inference

```python
import pandas as pd
from predict_model import OptiPluaPredictor

predictor = OptiPluaPredictor()
timetable = pd.read_csv("data/raw_schedules_test.csv")  # one timetable (many rows)
score = predictor.predict(timetable)[0]                 # single 0–100 score
```

`predict()` aggregates the input DataFrame with the **same** `aggregate_timetable`
used at training time, then runs the model. To rank several variants, use
[`scorer.TimetableScorer.rank_variants(method="ml")`](../scorer.py).

## Human-in-the-Loop (roadmap)

[`src/feedback_handler.py`](../src/feedback_handler.py) logs explicit (star rating)
and implicit (export/edit) feedback with weights (1.0 heuristic, 2.0 implicit,
5.0 explicit). A future retraining step can use these weights to let the model
diverge from the heuristic toward real user preferences.

## Related files

| File | Purpose |
|---|---|
| `generate_ml_dataset.py` | builds the timetable-level dataset |
| `models/feature_engineering.py` | aggregation & feature vector |
| `train_model.py` | training & evaluation |
| `predict_model.py` | inference wrapper |
| `scorer.py` | variant ranking |
