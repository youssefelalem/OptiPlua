"""
Build the ML training set from the SAME distribution used at inference.

For every establishment type we generate many timetable variants with the app's
own simulator, score each with the app's own heuristic, and aggregate it into
the timetable-level feature vector. This removes the train/serve mismatch that
made the model output a near-constant score on real variants.

Output: data/ml_timetable_dataset.csv  (one row per timetable)
"""

import os
import pandas as pd

from simulator import generer_n_variantes
from models.feature_engineering import aggregate_timetable

DATA_DIR = 'data'
OUTPUT = os.path.join(DATA_DIR, 'ml_timetable_dataset.csv')

TYPES = ['Ecole_Standard', 'Universite', 'Centre_Soutien']
N_PER_TYPE = 30
MAX_RETRIES = 150


def main():
    ens = pd.read_csv(os.path.join(DATA_DIR, 'enseignants_data.csv'))
    sal = pd.read_csv(os.path.join(DATA_DIR, 'salles_data.csv'))
    mat = pd.read_csv(os.path.join(DATA_DIR, 'matieres_data.csv'))
    cls = pd.read_csv(os.path.join(DATA_DIR, 'classes_data.csv'))

    rows = []
    for i, etype in enumerate(TYPES):
        e = ens[ens.Type_Etablissement == etype]
        s = sal[sal.Type_Etablissement == etype]
        m = mat[mat.Type_Etablissement == etype]
        c = cls[cls.Type_Etablissement == etype]
        if len(c) == 0:
            print(f"  [skip] {etype}: no classes")
            continue

        print(f"  Generating {N_PER_TYPE} variants for {etype}...")
        variants = generer_n_variantes(
            e, s, m, c,
            n_variantes=N_PER_TYPE,
            max_retries=MAX_RETRIES,
            base_seed=1000 * (i + 1),
        )
        for df_emp, score, _ in variants:
            feat = aggregate_timetable(df_emp)
            feat['Score'] = float(score)
            feat['Type_Etablissement'] = etype
            rows.append(feat)
        scores = [round(v[1], 1) for v in variants]
        print(f"    -> {len(variants)} timetables, heuristic scores {min(scores)}..{max(scores)}")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT, index=False)
    print(f"\nSaved {len(df)} timetables to {OUTPUT}")
    print(f"Score: min={df.Score.min():.2f} max={df.Score.max():.2f} "
          f"mean={df.Score.mean():.2f} std={df.Score.std():.2f}")


if __name__ == "__main__":
    main()
