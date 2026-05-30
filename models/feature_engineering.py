
import os
import warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

warnings.filterwarnings("ignore")

MODELS_DIR = os.path.dirname(__file__)
ARTEFACTS_PATH = os.path.join(MODELS_DIR, "preprocessing_artefacts.joblib")

COLS_CATEGORIQUES = ["Type_Etablissement", "Nom_Matiere", "Type_Salle", "Jour", "Niveau"]
COLS_NUMERIQUES = ["Nb_Etudiants", "Capacite_Salle", "Nb_Tentatives"]

def preprocess_data(df, is_training=True):
    df = df.copy()
    
    # 1. Temporal Features
    df['H_Start'] = df['Heure_Debut'].apply(lambda x: int(x.split(':')[0]))
    df['Est_Matin'] = (df['H_Start'] < 12).astype(int)
    
    # 2. Logistical Features
    df['Taux_Remplissage'] = df['Nb_Etudiants'] / df['Capacite_Salle']
    df['Pression_Planif'] = np.log1p(df['Nb_Tentatives'])
    
    # 3. Aggregated Features (The "Quality" signals)
    # Teacher Gaps (Window Hours)
    teacher_gaps = []
    for (prof, jour), group in df.groupby(['ID_Enseignant', 'Jour']):
        group = group.sort_values('H_Start')
        g = 0
        recs = group.to_dict('records')
        for i in range(len(recs)-1):
            gap = recs[i+1]['H_Start'] - int(recs[i]['Heure_Fin'].split(':')[0])
            if gap > 0: g += gap
        for idx in group.index:
            df.at[idx, 'Teacher_Day_Gap'] = g

    # Room Utilization Consistency
    room_avg_util = df.groupby('ID_Salle')['Taux_Remplissage'].transform('mean')
    df['Room_Avg_Util'] = room_avg_util

    # 4. Encoding
    if is_training:
        artefacts = {'encoders': {}, 'scaler': MinMaxScaler()}
        for col in COLS_CATEGORIQUES:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            artefacts['encoders'][col] = le
        
        num_cols = COLS_NUMERIQUES + ['Taux_Remplissage', 'Pression_Planif', 'Teacher_Day_Gap', 'Room_Avg_Util']
        df[num_cols] = artefacts['scaler'].fit_transform(df[num_cols])
        joblib.dump(artefacts, ARTEFACTS_PATH)
    else:
        artefacts = joblib.load(ARTEFACTS_PATH)
        for col in COLS_CATEGORIQUES:
            le = artefacts['encoders'][col]
            # Handle unseen labels
            df[col] = df[col].astype(str).map(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
        
        num_cols = COLS_NUMERIQUES + ['Taux_Remplissage', 'Pression_Planif', 'Teacher_Day_Gap', 'Room_Avg_Util']
        df[num_cols] = artefacts['scaler'].transform(df[num_cols])

    # Final feature selection
    features = COLS_CATEGORIQUES + num_cols + ['Est_Matin']
    X = df[features]
    y = df['Score'] if 'Score' in df.columns else None
    
    # Sample Weight logic (Default 1.0 for bootstrap, higher for human feedback)
    weights = df['User_Weight'] if 'User_Weight' in df.columns else np.ones(len(df))
    
    return X, y, weights

if __name__ == "__main__":
    # Test with current data
    raw_data = pd.read_csv(os.path.join(MODELS_DIR, '../data/raw_schedules_test.csv'))
    # Mock score for testing if missing
    if 'Score' not in raw_data.columns: raw_data['Score'] = 80.0
    X, y, w = preprocess_data(raw_data)
    print(f"Features processed. Shape: {X.shape}")
