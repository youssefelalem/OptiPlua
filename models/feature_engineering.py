"""
OptiPlua — Feature Engineering (TIMETABLE level).

The quality score describes a *whole* timetable, not a single session. Training
on individual session rows had no learnable signal (R2 ~ 0): every row of a
timetable carried the same constant score while its per-row features could not
determine that aggregate value.

This module collapses the many session rows of one timetable into a single
feature vector. The features deliberately mirror the four penalty terms of the
heuristic scorer (`simulator.calculer_score_emploi`):

    score = 100 * (1 - total_penalty / (5 * n_sessions))
    total_penalty = 2.0 * teacher_gaps
                  + 2.5 * class_gaps
                  + 1.0 * daily_overloads
                  + 1.5 * under_filled_rooms

Because the model is trained on timetables produced by the *same* simulator and
labelled by the *same* heuristic used at inference time, predictions both
discriminate between variants and stay on the heuristic's 0-100 scale.

`aggregate_timetable` is used for training (one example per generated timetable)
and for inference (the whole DataFrame passed in is one timetable).
"""

import numpy as np
import pandas as pd

# Order matters: this is the exact column order the model is fitted on.
TIMETABLE_FEATURES = [
    'teacher_gap_per_session',  # teacher window-hours, per session
    'class_gap_per_session',    # student window-hours, per session
    'overload_per_session',     # (class, day) blocks with > 4 sessions, per session
    'low_util_per_session',     # rooms filled < 40%, per session
    'avg_util',                 # mean room occupancy rate
    'n_sessions',               # timetable size
]


def _hour(value) -> int:
    """'08:00' / '08:00-10:00' -> 8 (hour of day)."""
    return int(str(value).split(':')[0])


def _sum_gaps(g: pd.DataFrame, key: str) -> float:
    """Total positive window-hours within each (key, day) group."""
    if key not in g.columns:
        return 0.0
    total = 0.0
    for _, grp in g.groupby([key, 'Jour']):
        recs = grp.sort_values('_h_start')[['_h_start', '_h_end']].to_dict('records')
        for i in range(len(recs) - 1):
            gap = recs[i + 1]['_h_start'] - recs[i]['_h_end']
            if gap > 0:
                total += gap
    return total


def aggregate_timetable(df: pd.DataFrame) -> dict:
    """Collapse one timetable (many session rows) into a single feature vector."""
    n = len(df)
    if n == 0:
        return {f: 0.0 for f in TIMETABLE_FEATURES}

    g = df.copy()
    g['_h_start'] = g['Heure_Debut'].map(_hour)
    g['_h_end'] = g['Heure_Fin'].map(_hour)
    g['_util'] = g['Nb_Etudiants'] / g['Capacite_Salle']

    teacher_gaps = _sum_gaps(g, 'ID_Enseignant')
    class_gaps = _sum_gaps(g, 'ID_Classe')

    # Daily overload: (class, day) blocks holding more than 4 sessions.
    if 'ID_Classe' in g.columns:
        sizes = g.groupby(['ID_Classe', 'Jour']).size()
        overloads = int((sizes > 4).sum())
    else:
        overloads = 0

    # Under-filled rooms: occupancy below 40%.
    low_util = int((g['_util'] < 0.4).sum())

    return {
        'teacher_gap_per_session': teacher_gaps / n,
        'class_gap_per_session': class_gaps / n,
        'overload_per_session': overloads / n,
        'low_util_per_session': low_util / n,
        'avg_util': float(g['_util'].mean()),
        'n_sessions': float(n),
    }


def features_for_timetable(df: pd.DataFrame) -> pd.DataFrame:
    """Single-row feature frame for one timetable (inference)."""
    return pd.DataFrame([aggregate_timetable(df)], columns=TIMETABLE_FEATURES)


def build_timetable_dataset(df: pd.DataFrame, group_key: str = 'Version'):
    """Build (X, y) at the timetable level.

    Two input shapes are accepted:
      * pre-aggregated  — already has the TIMETABLE_FEATURES columns (+ Score);
      * session-level   — many rows per timetable, grouped by ``group_key``.
    """
    if set(TIMETABLE_FEATURES).issubset(df.columns):
        X = df[TIMETABLE_FEATURES].copy()
        y = df['Score'].astype(float) if 'Score' in df.columns else None
        return X, y

    has_score = 'Score' in df.columns
    rows, scores = [], []
    grouped = df.groupby(group_key) if group_key in df.columns else [(None, df)]
    for _, grp in grouped:
        rows.append(aggregate_timetable(grp))
        if has_score:
            scores.append(float(grp['Score'].iloc[0]))

    X = pd.DataFrame(rows, columns=TIMETABLE_FEATURES)
    y = pd.Series(scores, name='Score') if has_score else None
    return X, y


if __name__ == "__main__":
    import os
    here = os.path.dirname(__file__)
    path = os.path.join(here, '../data/ml_timetable_dataset.csv')
    if os.path.exists(path):
        X, y = build_timetable_dataset(pd.read_csv(path))
        print(f"Timetables: {len(X)} | features: {X.shape[1]}")
        print(X.describe().round(3))
        if y is not None:
            print(f"Score: min={y.min():.2f} max={y.max():.2f} std={y.std():.2f}")
