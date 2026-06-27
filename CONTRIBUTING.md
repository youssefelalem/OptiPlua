# Contributing to OptiPlua

Thanks for your interest in OptiPlua! This is an academic project (Master's PFE),
but contributions and suggestions are welcome.

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Project conventions

- **Language**: code and comments are in French; documentation (`README.md`,
  `docs/`) is in English. The LaTeX report (`rapport/`) is in French.
- **Style**: keep functions small and focused; match the surrounding code's
  naming and comment density. Pure logic lives in modules (`simulator.py`,
  `models/`, `scorer.py`); `app.py` is the Streamlit UI layer only.
- **ML granularity**: the model operates at the **timetable** level. Any new
  feature must be computed from a whole timetable (see
  [`docs/ML_PIPELINE.md`](docs/ML_PIPELINE.md)) — never per session.

## Reproducing the pipeline

```bash
python generate_ml_dataset.py   # rebuild the training set
python train_model.py           # retrain and refresh models/metrics.json
```

If you change the feature set in `models/feature_engineering.py`, regenerate the
dataset and retrain so that `feature_names.pkl` stays consistent with the model.

## Pull requests

1. Create a feature branch.
2. Keep changes scoped and described.
3. Make sure `python train_model.py` runs cleanly and metrics do not regress.

## Authors

Youssef EL ALEM & Douae MOUSSAOUI — Faculté des Sciences Ben M'Sik, UH2C.
