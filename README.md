<div align="center">

# OptiPlua

### AI-Powered School Timetable Generation & Optimization

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-Model-FF6600?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-16A34A?style=for-the-badge)](LICENSE)
[![Model R²](https://img.shields.io/badge/Model%20R²-0.9996-1D4ED8?style=for-the-badge)]()

**OptiPlua** generates, evaluates and ranks school timetables for Moroccan
educational institutions — schools, tutoring centers and universities — by
combining a **constraint-based heuristic engine** with a **machine-learning
quality model (XGBoost)**.

*Master's Final-Year Project (PFE) — **Youssef EL ALEM** & **Douae MOUSSAOUI***
*Faculté des Sciences Ben M'Sik · Université Hassan II de Casablanca*

</div>

---

## Overview

Timetabling is an NP-hard combinatorial problem: courses must be assigned to time
slots, rooms and teachers under hard constraints, while maximizing pedagogical
quality. OptiPlua addresses **both** sides of the problem:

1. **Generation** — a randomized heuristic engine produces valid timetable variants.
2. **Evaluation** — an interpretable quality score (0–100) and an XGBoost model rank
   those variants.

```
Synthetic data  →  Heuristic engine  →  Quality scoring  →  Streamlit app
 (4 datasets)       (9 hard constraints)   (heuristic + ML)     (rank & export)
```

## Highlights

| Feature | Description |
|---|---|
| 🏫 **Multi-institution** | Schools, tutoring centers and universities, each with its own slots & rules |
| ⚙️ **Heuristic engine** | 9 hard constraints (C1–C9), seed-based variant generation |
| 📊 **Interpretable score** | `Score = 100 × (1 − penalty / (5·n_sessions))` from 4 pedagogical penalties |
| 🤖 **ML scorer** | Timetable-level XGBoost regressor, **R² = 0.9996** |
| 🖥️ **Web app** | Streamlit dashboard: configure, generate, rank, export to PDF |

## The ML story: target granularity matters

A first attempt trained the model at the **session** level — each of ~182,000
rows carried the *constant* score of its whole timetable. The model could only
learn the global mean (**R² ≈ 0**, near-constant predictions, **no discrimination**
between variants).

The fix was to model at the **whole-timetable** level: collapse each timetable's
sessions into a single feature vector that mirrors the four penalty terms of the
score. Same simulator + same heuristic for both training and inference → **no
train/serve mismatch**.

| | Per-session (initial) | Per-timetable (final) |
|---|---|---|
| Granularity | ~182,000 rows | 90 timetables |
| **R² (test)** | ≈ 0 (negative) | **0.9996** |
| RMSE | ≈ 1.08 | **0.497** |
| Discrimination | ❌ none | ✅ clear |

> 📄 The full methodology is documented in the LaTeX report under [`rapport/`](rapport/)
> and in [`docs/ML_PIPELINE.md`](docs/ML_PIPELINE.md).

## Project structure

```
OptiPlua/
├── app.py                       # Streamlit web application
├── simulator.py                 # heuristic generation + heuristic quality score
├── generate_ml_dataset.py       # builds the timetable-level training set
├── train_model.py               # trains & evaluates the XGBoost model
├── predict_model.py             # inference (one score per timetable)
├── scorer.py                    # ranks variants (heuristic or ML)
├── create_rapport.py            # PDF report generation
├── models/
│   ├── feature_engineering.py   # timetable-level feature aggregation
│   ├── optiplua_model.pkl       # trained model
│   ├── feature_names.pkl        # feature order
│   └── metrics.json             # evaluation metrics
├── data/                        # synthetic datasets, ML dataset, EDA figures
├── src/
│   ├── bootstrap_data.py        # (legacy) session-level data generator
│   └── feedback_handler.py      # Human-in-the-Loop feedback logging
├── notebooks/                   # data generation, EDA, simulation
├── logo/                        # brand assets (SVG)
├── rapport/                     # LaTeX PFE report (+ figures & image prompts)
├── presentation/                # poster & slide-deck generation prompts
├── docs/                        # technical documentation
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone https://github.com/youssefelalem/OptiPlua.git
cd OptiPlua

python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

Reproduce the full ML pipeline in three commands:

```bash
python generate_ml_dataset.py   # 1. build data/ml_timetable_dataset.csv
python train_model.py           # 2. train & save models/optiplua_model.pkl
streamlit run app.py            # 3. launch the web app
```

Score a timetable programmatically:

```python
import pandas as pd
from predict_model import OptiPluaPredictor

predictor = OptiPluaPredictor()
timetable = pd.read_csv("data/raw_schedules_test.csv")   # one timetable
score = predictor.predict(timetable)[0]
print(f"Quality score: {score:.1f}/100")
```

Rank generated variants with the ML scorer:

```python
from simulator import generer_n_variantes
from scorer import TimetableScorer

variants = generer_n_variantes(ens, sal, mat, cls, n_variantes=5)
ranked = TimetableScorer().rank_variants(variants, method="ml")
```

## Results

- **R² = 0.9996**, **RMSE = 0.497** on held-out timetables (90 samples).
- Quality scores span **15.96 → 96.69** across institution types.
- Most important features: `teacher_gap_per_session` (0.80), `class_gap_per_session`
  (0.19) — consistent with how the heuristic score is built.

## Authors

| Name | Contribution |
|---|---|
| **Youssef EL ALEM** | Data engineering, heuristic simulator, ML pipeline |
| **Douae MOUSSAOUI** | EDA, scoring design, visualization & reporting |

Supervised at the **Faculté des Sciences Ben M'Sik**, Université Hassan II de
Casablanca — Master's Final-Year Project, 2025/2026.

## License

Released under the [MIT License](LICENSE).

<div align="center">
<sub>OptiPlua — Intelligent scheduling for education.</sub>
</div>
