
import pandas as pd
import random
import ast
import time
from collections import defaultdict
from tqdm import tqdm
import os

# --- Configuration ---
DATA_DIR = 'data'
OUTPUT_FILE = os.path.join(DATA_DIR, 'bootstrap_schedules.csv')
NB_VERSIONS = 100  # Number of full timetables to generate
MAX_RETRIES = 300

# --- Load Data ---
print("[1/3] Loading base data...")
df_enseignants = pd.read_csv(os.path.join(DATA_DIR, 'enseignants_data.csv'))
df_salles      = pd.read_csv(os.path.join(DATA_DIR, 'salles_data.csv'))
df_matieres    = pd.read_csv(os.path.join(DATA_DIR, 'matieres_data.csv'))
df_classes     = pd.read_csv(os.path.join(DATA_DIR, 'classes_data.csv'))

def safe_parse_list(val):
    try:
        return ast.literal_eval(val) if isinstance(val, str) else []
    except (ValueError, SyntaxError):
        return []

df_enseignants['Matieres'] = df_enseignants['Matieres'].apply(safe_parse_list)
df_enseignants['Niveaux_Autorises'] = df_enseignants['Niveaux_Autorises'].apply(safe_parse_list)
df_enseignants['Creneaux_Indisponibles'] = df_enseignants['Creneaux_Indisponibles'].apply(safe_parse_list)

# --- Indexing ---
JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']
HEURES = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00']
CRENEAUX = [f"{j}_{h}" for j in JOURS for h in HEURES]

matieres_par_type = defaultdict(list)
for _, row in df_matieres.iterrows():
    matieres_par_type[row['Type_Etablissement']].append(row['ID_Matiere'])

matiere_info = df_matieres.set_index('ID_Matiere').to_dict('index')

salles_par_type = defaultdict(list)
for _, row in df_salles.iterrows():
    salles_par_type[row['Type_Etablissement']].append(row.to_dict())

profs_par_matiere = defaultdict(list)
for _, row in df_enseignants.iterrows():
    for mat in row['Matieres']:
        profs_par_matiere[(row['Type_Etablissement'], mat)].append(row.to_dict())

# --- Simulation Engine ---
TYPES_LABO = {'Labo_Science', 'Labo_Informatique', 'Laboratoire'}

def verifier_contraintes(id_prof, id_salle, id_classe, creneau,
                         heures_prof, indispo_prof, max_heures_prof,
                         occ_prof, occ_salle, occ_classe):
    if creneau in occ_prof.get(id_prof, set()): return False, 'C1'
    if creneau in occ_salle.get(id_salle, set()): return False, 'C2'
    if creneau in occ_classe.get(id_classe, set()): return False, 'C3'
    if creneau in indispo_prof: return False, 'C4'
    if heures_prof.get(id_prof, 0) >= max_heures_prof: return False, 'C5'
    return True, ''

def generer_emploi(df_classes, seed):
    random.seed(seed)
    emploi = []
    occ_prof, occ_salle, occ_classe = defaultdict(set), defaultdict(set), defaultdict(set)
    heures_prof = defaultdict(int)
    
    classes_shuffled = df_classes.sample(frac=1, random_state=seed).to_dict('records')
    
    for classe in classes_shuffled:
        id_classe = classe['ID_Classe']
        type_etab = classe['Type_Etablissement']
        niveau = classe['Niveau']
        nb_etudiants = classe['Nombre_Etudiants']
        
        for id_mat in matieres_par_type.get(type_etab, []):
            info = matiere_info[id_mat]
            nb_seances = int(info['Heures_Hebdo_Requises'] // 2)
            
            profs_compat = [p for p in profs_par_matiere.get((type_etab, info['Nom_Matiere']), []) 
                            if niveau in p['Niveaux_Autorises']]
            
            salles_du_type = salles_par_type.get(type_etab, [])
            if info['Necessite_Labo']:
                salles_filtrees = [s for s in salles_du_type if s['Type_Salle'] in TYPES_LABO]
            else:
                salles_filtrees = salles_du_type
                
            salles_compat = [s for s in salles_filtrees if s['Capacite'] >= nb_etudiants]
            if not salles_compat:
                salles_compat = sorted(salles_filtrees, key=lambda x: x['Capacite'], reverse=True)[:3]

            if not profs_compat or not salles_compat: continue

            for _ in range(nb_seances):
                assigne, t = False, 0
                while not assigne and t < MAX_RETRIES:
                    t += 1
                    creneau, prof, salle = random.choice(CRENEAUX), random.choice(profs_compat), random.choice(salles_compat)
                    valide, _ = verifier_contraintes(prof['ID_Enseignant'], salle['ID_Salle'], id_classe, creneau,
                                                     heures_prof, set(prof['Creneaux_Indisponibles']), 
                                                     prof['Heures_Max_Par_Semaine'], occ_prof, occ_salle, occ_classe)
                    if valide:
                        occ_prof[prof['ID_Enseignant']].add(creneau)
                        occ_salle[salle['ID_Salle']].add(creneau)
                        occ_classe[id_classe].add(creneau)
                        heures_prof[prof['ID_Enseignant']] += 2
                        
                        p = creneau.split('_')
                        emploi.append({
                            'ID_Classe': id_classe, 'Type_Etablissement': type_etab, 'Niveau': niveau,
                            'Nb_Etudiants': nb_etudiants, 'Nom_Matiere': info['Nom_Matiere'],
                            'ID_Enseignant': prof['ID_Enseignant'], 'ID_Salle': salle['ID_Salle'],
                            'Capacite_Salle': salle['Capacite'], 'Type_Salle': salle['Type_Salle'],
                            'Jour': p[0], 'Heure_Debut': p[1].split('-')[0], 'Heure_Fin': p[1].split('-')[1],
                            'Nb_Tentatives': t, 'Version': seed
                        })
                        assigne = True
    return pd.DataFrame(emploi)

# --- Heuristic Scoring ---
def score_timetable(df):
    if df.empty: return 0.0
    pen_trous = 0
    df['H_Start'] = df['Heure_Debut'].apply(lambda x: int(x.split(':')[0]))
    df['H_End'] = df['Heure_Fin'].apply(lambda x: int(x.split(':')[0]))
    
    for (_, _), group in df.groupby(['ID_Enseignant', 'Jour']):
        group = group.sort_values('H_Start')
        recs = group.to_dict('records')
        for i in range(len(recs)-1):
            gap = recs[i+1]['H_Start'] - recs[i]['H_End']
            if gap > 0: pen_trous += gap * 2
            
    df['Util'] = df['Nb_Etudiants'] / df['Capacite_Salle']
    pen_salles = len(df[df['Util'] < 0.4]) * 1.5
    
    total_pen = pen_trous + pen_salles
    score = max(0.0, 100.0 * (1 - (total_pen / (len(df) * 3.0))))
    return round(score, 2)

# --- Main Pipeline ---
print(f"[2/3] Generating {NB_VERSIONS} schedule versions...")
all_data = []
for i in tqdm(range(NB_VERSIONS)):
    df_ver = generer_emploi(df_classes, seed=42+i)
    if not df_ver.empty:
        s = score_timetable(df_ver)
        df_ver['Score'] = s
        all_data.append(df_ver)

df_final = pd.concat(all_data, ignore_index=True)
df_final.to_csv(OUTPUT_FILE, index=False)
print(f"[3/3] Done! Saved {len(df_final)} sessions to {OUTPUT_FILE}")
