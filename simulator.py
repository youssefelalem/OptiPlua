import pandas as pd
import random
import ast
import time
from collections import defaultdict
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

from constraints import verifier_contraintes, calculer_score_emploi, TYPES_LABO

class ScheduleSimulator:
    def __init__(self, data_path='./'):
        """
        Initialise le simulateur avec les données CSV.
        """
        self.data_path = data_path
        self.JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']
        self.HEURES = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00']
        self.CRENEAUX = [f"{j}_{h}" for j in self.JOURS for h in self.HEURES]
        
        self.load_data()
        self.build_indexes()

    def load_data(self):
        """Charge les fichiers CSV et parse les listes."""
        self.df_enseignants = pd.read_csv(f'{self.data_path}enseignants_data.csv')
        self.df_salles = pd.read_csv(f'{self.data_path}salles_data.csv')
        self.df_matieres = pd.read_csv(f'{self.data_path}matieres_data.csv')
        self.df_classes = pd.read_csv(f'{self.data_path}classes_data.csv')

        def safe_parse_list(val):
            try:
                return ast.literal_eval(val) if isinstance(val, str) else []
            except (ValueError, SyntaxError):
                return []

        for col in ['Matieres', 'Niveaux_Autorises', 'Creneaux_Indisponibles']:
            self.df_enseignants[col] = self.df_enseignants[col].apply(safe_parse_list)

    def build_indexes(self):
        """Construit des index rapides pour l'algorithme heuristique."""
        # Sécurité : S'assurer que les colonnes de listes sont bien parsées 
        # (Utile si les DataFrames sont injectés directement depuis Streamlit)
        def robust_parse(val):
            if isinstance(val, str) and val.strip().startswith('['):
                try:
                    return ast.literal_eval(val)
                except (ValueError, SyntaxError):
                    return []
            return val if isinstance(val, list) else []

        for col in ['Matieres', 'Niveaux_Autorises', 'Creneaux_Indisponibles']:
            if col in self.df_enseignants.columns:
                self.df_enseignants[col] = self.df_enseignants[col].apply(robust_parse)
        self.matieres_par_type = defaultdict(list)
        for _, row in self.df_matieres.iterrows():
            self.matieres_par_type[row['Type_Etablissement']].append(row['ID_Matiere'])

        self.matiere_info = self.df_matieres.set_index('ID_Matiere').to_dict('index')

        self.salles_par_type = defaultdict(list)
        for _, row in self.df_salles.iterrows():
            self.salles_par_type[row['Type_Etablissement']].append(row.to_dict())

        self.profs_par_matiere = defaultdict(list)
        for _, row in self.df_enseignants.iterrows():
            for mat in row['Matieres']:
                self.profs_par_matiere[(row['Type_Etablissement'], mat)].append(row.to_dict())

    def generer_emploi_du_temps(self, max_retries=300):
        """
        Moteur Heuristique v2.1.
        Génère un emploi du temps complet en respectant les contraintes dures.
        """
        emploi = []
        echecs = []
        stats_raison = defaultdict(int)

        occupations_prof = defaultdict(set)
        occupations_salle = defaultdict(set)
        occupations_classe = defaultdict(set)
        heures_prof = defaultdict(int)

        # On mélange les classes pour éviter les biais systématiques
        classes_shuffled = self.df_classes.sample(frac=1, random_state=42).to_dict('records')

        for classe in classes_shuffled:
            id_classe = classe['ID_Classe']
            type_etab = classe['Type_Etablissement']
            niveau = classe['Niveau']
            nb_etudiants = classe['Nombre_Etudiants']

            matieres_dispo = self.matieres_par_type.get(type_etab, [])
            for id_matiere_cible in matieres_dispo:
                info_mat = self.matiere_info[id_matiere_cible]
                nom_matiere = info_mat['Nom_Matiere']
                necessite_labo = info_mat['Necessite_Labo']
                heures_requises = info_mat['Heures_Hebdo_Requises']
                nb_seances = int(heures_requises // 2)

                for _ in range(nb_seances):
                    # Profs compatibles
                    profs_compat = [
                        p for p in self.profs_par_matiere.get((type_etab, nom_matiere), [])
                        if niveau in p['Niveaux_Autorises']
                    ]
                    if not profs_compat:
                        echecs.append({'ID_Classe': id_classe, 'Raison': 'aucun_prof_compatible', 'ID_Matiere': id_matiere_cible})
                        continue

                    # Salles filtrées par type (Labo vs Standard)
                    salles_du_type = self.salles_par_type.get(type_etab, [])
                    if necessite_labo:
                        salles_filtrees = [s for s in salles_du_type if s['Type_Salle'] in TYPES_LABO]
                        if not salles_filtrees:
                            echecs.append({'ID_Classe': id_classe, 'Raison': 'C6_aucun_labo_disponible', 'ID_Matiere': id_matiere_cible})
                            continue
                    else:
                        salles_filtrees = salles_du_type

                    # Contrainte Capacité avec Fallback
                    salles_compat = [s for s in salles_filtrees if s['Capacite'] >= nb_etudiants]
                    if not salles_compat:
                        salles_compat = sorted(salles_filtrees, key=lambda s: s['Capacite'], reverse=True)[:3]
                        stats_raison['C7_capacite_insuffisante_fallback'] += 1
                    
                    if not salles_compat:
                        echecs.append({'ID_Classe': id_classe, 'Raison': 'C7_aucune_salle_compatible'})
                        continue

                    # Tentatives de placement
                    assigne = False
                    tentatives = 0
                    while not assigne and tentatives < max_retries:
                        tentatives += 1
                        creneau = random.choice(self.CRENEAUX)
                        prof = random.choice(profs_compat)
                        salle = random.choice(salles_compat)

                        id_prof = prof['ID_Enseignant']
                        id_salle = salle['ID_Salle']
                        max_h = prof['Heures_Max_Par_Semaine']
                        indispo = set(prof['Creneaux_Indisponibles'])

                        valide, raison = verifier_contraintes(
                            id_prof, id_salle, id_classe, creneau,
                            heures_prof, indispo, max_h,
                            occupations_prof, occupations_salle, occupations_classe
                        )

                        if valide:
                            occupations_prof[id_prof].add(creneau)
                            occupations_salle[id_salle].add(creneau)
                            occupations_classe[id_classe].add(creneau)
                            heures_prof[id_prof] += 2

                            parts = creneau.split('_')
                            jour = parts[0]
                            heure_debut, heure_fin = parts[1].split('-')

                            emploi.append({
                                'ID_Classe': id_classe,
                                'Type_Etablissement': type_etab,
                                'Niveau': niveau,
                                'Nb_Etudiants': nb_etudiants,
                                'ID_Matiere': id_matiere_cible,
                                'Nom_Matiere': nom_matiere,
                                'ID_Enseignant': id_prof,
                                'Nom_Enseignant': prof['Nom_Enseignant'],
                                'ID_Salle': id_salle,
                                'Capacite_Salle': salle['Capacite'],
                                'Type_Salle': salle['Type_Salle'],
                                'Creneau': creneau,
                                'Jour': jour,
                                'Heure_Debut': heure_debut,
                                'Heure_Fin': heure_fin,
                                'Nb_Tentatives': tentatives
                            })
                            assigne = True
                        else:
                            stats_raison[raison] += 1

                    if not assigne:
                        echecs.append({'ID_Classe': id_classe, 'Raison': f'max_retries_{max_retries}', 'ID_Matiere': id_matiere_cible})

        return pd.DataFrame(emploi), pd.DataFrame(echecs), dict(stats_raison)

    def generate_candidates(self, n=100, max_retries=300):
        """Génère n candidats en mémoire."""
        candidates = []
        print(f"[Memory] Génération de {n} candidats...")
        
        for i in tqdm(range(1, n + 1)):
            random.seed(int(time.time()) + i)
            df_gen, _, _ = self.generer_emploi_du_temps(max_retries=max_retries)
            score, _ = calculer_score_emploi(df_gen)
            df_gen['Score'] = score
            df_gen['Candidate_ID'] = i
            candidates.append(df_gen)
            
        if not candidates:
            return pd.DataFrame(columns=['Candidate_ID', 'Score', 'ID_Classe', 'Nom_Matiere', 'ID_Enseignant', 'ID_Salle', 'Jour', 'Heure_Debut'])
        return pd.concat(candidates, ignore_index=True)

if __name__ == "__main__":
    # Test rapide
    sim = ScheduleSimulator()
    df_emploi, df_echecs, stats = sim.generer_emploi_du_temps()
    score, _ = calculer_score_emploi(df_emploi)
    print(f"Emploi généré: {len(df_emploi)} séances")
    print(f"Score final: {score}")
    print(f"Échecs: {len(df_echecs)}")
