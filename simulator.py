"""
OptiPlua — Moteur Heuristique de Génération d'Emplois du Temps
Extrait de notebooks/simulation.ipynb, paramétré pour générer N variantes.
"""

import pandas as pd
import random
import ast
from collections import defaultdict
from typing import Tuple, List, Dict, Any


JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']

HEURES_PAR_TYPE = {
    'Ecole_Standard': ['08:00-10:00', '10:00-12:00', '14:00-16:00'],
    'Centre_Soutien': ['19:00-21:00', '21:00-22:00'],
    'Universite':     ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00'],
}
HEURES_DEFAULT = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00']

ALL_HEURES = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00', '19:00-21:00', '21:00-22:00']
CRENEAUX = [f"{j}_{h}" for j in JOURS for h in ALL_HEURES]

TYPES_LABO = {'Labo_Science', 'Labo_Informatique', 'Laboratoire'}

HEURE_TO_INT = {
    '08:00-10:00': 8, '10:00-12:00': 10,
    '14:00-16:00': 14, '16:00-18:00': 16,
    '19:00-21:00': 19, '21:00-22:00': 21,
}

SLOT_DURATION = {
    '08:00-10:00': 2, '10:00-12:00': 2,
    '14:00-16:00': 2, '16:00-18:00': 2,
    '19:00-21:00': 2, '21:00-22:00': 1,
}

MAX_HEURES_JOUR_PROF = 8


def _get_slot_duration(creneau: str) -> int:
    """Retourne la duree d'un creneau en heures (ex: '19:00-21:00' -> 2, '21:00-22:00' -> 1)."""
    heure = creneau.split('_', 1)[1] if '_' in creneau else creneau
    return SLOT_DURATION.get(heure, 2)


def safe_parse_list(val) -> list:
    try:
        return ast.literal_eval(val) if isinstance(val, str) else []
    except (ValueError, SyntaxError):
        return []


def _get_creneaux_for_type(type_etab: str, heures_par_type: dict = None) -> list:
    hp = heures_par_type or HEURES_PAR_TYPE
    heures = hp.get(type_etab, HEURES_DEFAULT)
    return [f"{j}_{h}" for j in JOURS for h in heures]


def build_indexes(
    df_enseignants: pd.DataFrame,
    df_salles: pd.DataFrame,
    df_matieres: pd.DataFrame,
) -> Tuple[dict, dict, dict, dict]:
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

    return matieres_par_type, matiere_info, salles_par_type, profs_par_matiere


def _get_consecutive_hours(occupations: set, jour: str) -> int:
    slots_today = []
    for c in occupations:
        parts = c.split('_', 1)
        if parts[0] == jour and parts[1] in HEURE_TO_INT:
            slots_today.append(HEURE_TO_INT[parts[1]])
    if not slots_today:
        return 0
    slots_today.sort()
    # Build a list of (start_hour, duration) for sorting
    slot_details = []
    for c in occupations:
        parts = c.split('_', 1)
        if parts[0] == jour and parts[1] in HEURE_TO_INT:
            slot_details.append((HEURE_TO_INT[parts[1]], SLOT_DURATION.get(parts[1], 2)))
    if not slot_details:
        return 0
    slot_details.sort()
    first_dur = slot_details[0][1]
    max_consec = first_dur
    current_consec = first_dur
    for i in range(1, len(slot_details)):
        prev_start, prev_dur = slot_details[i-1]
        curr_start, curr_dur = slot_details[i]
        if curr_start == prev_start + prev_dur:
            current_consec += curr_dur
            max_consec = max(max_consec, current_consec)
        else:
            current_consec = curr_dur
    return max_consec


def _get_heures_jour(occupations: set, jour: str) -> int:
    count = 0
    for c in occupations:
        if c.startswith(jour + '_'):
            count += _get_slot_duration(c)
    return count


def verifier_contraintes(
    id_prof: str, id_salle: str, id_classe: str, creneau: str,
    heures_prof: dict, indispo_prof: set, max_heures_prof: int,
    occupations_prof: dict, occupations_salle: dict, occupations_classe: dict,
    max_consecutives: int = 0,
) -> Tuple[bool, str]:
    # C1: prof not double-booked
    if creneau in occupations_prof.get(id_prof, set()):
        return False, 'C1_prof_occupe'
    # C2: room not double-booked
    if creneau in occupations_salle.get(id_salle, set()):
        return False, 'C2_salle_occupee'
    # C3: class not double-booked
    if creneau in occupations_classe.get(id_classe, set()):
        return False, 'C3_classe_occupee'
    # C4: teacher unavailability
    if creneau in indispo_prof:
        return False, 'C4_indispo'
    # C5: max weekly hours
    if heures_prof.get(id_prof, 0) >= max_heures_prof:
        return False, 'C5_max_heures'

    jour = creneau.split('_')[0]

    # C8: max consecutive hours per teacher
    if max_consecutives > 0:
        test_occ = occupations_prof.get(id_prof, set()) | {creneau}
        consec = _get_consecutive_hours(test_occ, jour)
        if consec > max_consecutives:
            return False, 'C8_max_consecutives'

    # C9: max daily hours per teacher
    heures_jour = _get_heures_jour(occupations_prof.get(id_prof, set()), jour)
    slot_dur = _get_slot_duration(creneau)
    if heures_jour + slot_dur > MAX_HEURES_JOUR_PROF:
        return False, 'C9_max_heures_jour'

    return True, ''


def generer_emploi_du_temps(
    df_classes: pd.DataFrame,
    matieres_par_type: dict,
    matiere_info: dict,
    salles_par_type: dict,
    profs_par_matiere: dict,
    seed: int = 42,
    max_retries: int = 300,
    heures_par_type: dict = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    random.seed(seed)

    emploi: List[dict] = []
    echecs: List[dict] = []
    stats_raison: Dict[str, int] = defaultdict(int)

    occupations_prof = defaultdict(set)
    occupations_salle = defaultdict(set)
    occupations_classe = defaultdict(set)
    heures_prof: Dict[str, int] = defaultdict(int)

    classes_shuffled = df_classes.sample(frac=1, random_state=seed).to_dict('records')

    for classe in classes_shuffled:
        id_classe = classe['ID_Classe']
        type_etab = classe['Type_Etablissement']
        niveau = classe['Niveau']
        nb_etudiants = classe['Nombre_Etudiants']

        creneaux_type = _get_creneaux_for_type(type_etab, heures_par_type)

        matieres_dispo = matieres_par_type.get(type_etab, [])
        if not matieres_dispo:
            echecs.append({'ID_Classe': id_classe, 'Raison': 'aucune_matiere_type'})
            continue

        for id_matiere_cible in matieres_dispo:
            nom_matiere = matiere_info[id_matiere_cible]['Nom_Matiere']
            necessite_labo = matiere_info[id_matiere_cible]['Necessite_Labo']
            heures_requises = matiere_info[id_matiere_cible]['Heures_Hebdo_Requises']
            nb_seances = int(heures_requises // 2)

            for _ in range(nb_seances):
                profs_compat = [
                    p for p in profs_par_matiere.get((type_etab, nom_matiere), [])
                    if niveau in p['Niveaux_Autorises']
                ]
                if not profs_compat:
                    echecs.append({
                        'ID_Classe': id_classe,
                        'Raison': 'aucun_prof_compatible',
                        'ID_Matiere': id_matiere_cible,
                    })
                    continue

                salles_du_type = salles_par_type.get(type_etab, [])
                if necessite_labo:
                    salles_filtrees = [s for s in salles_du_type if s['Type_Salle'] in TYPES_LABO]
                    if not salles_filtrees:
                        echecs.append({
                            'ID_Classe': id_classe,
                            'Raison': 'C6_aucun_labo_disponible',
                            'ID_Matiere': id_matiere_cible,
                        })
                        continue
                else:
                    salles_filtrees = salles_du_type

                salles_compat = [s for s in salles_filtrees if s['Capacite'] >= nb_etudiants]
                if not salles_compat:
                    salles_compat = sorted(
                        salles_filtrees, key=lambda s: s['Capacite'], reverse=True
                    )[:3]
                    stats_raison['C7_capacite_insuffisante_fallback'] += 1
                if not salles_compat:
                    echecs.append({'ID_Classe': id_classe, 'Raison': 'C7_aucune_salle_compatible'})
                    continue

                assigne = False
                tentatives = 0

                while not assigne and tentatives < max_retries:
                    tentatives += 1
                    creneau = random.choice(creneaux_type)
                    prof = random.choice(profs_compat)
                    salle = random.choice(salles_compat)

                    id_prof = prof['ID_Enseignant']
                    id_salle = salle['ID_Salle']
                    max_h = prof['Heures_Max_Par_Semaine']
                    max_consec = prof.get('Heures_Max_Consecutives', 0)
                    indispo = set(c for c in prof['Creneaux_Indisponibles'] if c in CRENEAUX)

                    valide, raison = verifier_contraintes(
                        id_prof, id_salle, id_classe, creneau,
                        heures_prof, indispo, max_h,
                        occupations_prof, occupations_salle, occupations_classe,
                        max_consecutives=max_consec,
                    )

                    if valide:
                        occupations_prof[id_prof].add(creneau)
                        occupations_salle[id_salle].add(creneau)
                        occupations_classe[id_classe].add(creneau)
                        heures_prof[id_prof] += _get_slot_duration(creneau)

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
                            'Nb_Tentatives': tentatives,
                        })
                        assigne = True
                    else:
                        stats_raison[raison] += 1

                if not assigne:
                    echecs.append({
                        'ID_Classe': id_classe,
                        'Raison': f'max_retries_{max_retries}',
                        'ID_Matiere': id_matiere_cible,
                    })

    return pd.DataFrame(emploi), pd.DataFrame(echecs), dict(stats_raison)


def calculer_score_emploi(df_emploi: pd.DataFrame) -> Tuple[float, dict]:
    """
    Score de qualité (0-100) tenant compte des enseignants ET des élèves.
    """
    total_seances = len(df_emploi)
    if total_seances == 0:
        return 0.0, {}

    df_temp = df_emploi.copy()
    df_temp['H_Debut_Int'] = df_temp['Heure_Debut'].apply(lambda x: int(x.split(':')[0]))
    df_temp['H_Fin_Int'] = df_temp['Heure_Fin'].apply(lambda x: int(x.split(':')[0]))

    # 1. Gaps enseignants: -2 pts / heure de gap
    penalite_trous_profs = 0
    for (id_prof, jour), group in df_temp.groupby(['ID_Enseignant', 'Jour']):
        group = group.sort_values('H_Debut_Int')
        slots = group.to_dict('records')
        for i in range(len(slots) - 1):
            gap = slots[i + 1]['H_Debut_Int'] - slots[i]['H_Fin_Int']
            if gap > 0:
                penalite_trous_profs += gap * 2

    # 2. Gaps classes (élèves): -2.5 pts / heure de gap
    penalite_trous_classes = 0
    for (id_classe, jour), group in df_temp.groupby(['ID_Classe', 'Jour']):
        group = group.sort_values('H_Debut_Int')
        slots = group.to_dict('records')
        for i in range(len(slots) - 1):
            gap = slots[i + 1]['H_Debut_Int'] - slots[i]['H_Fin_Int']
            if gap > 0:
                penalite_trous_classes += gap * 2.5

    # 3. Surcharge journalière: -1 pt si classe a > 4 séances/jour
    seances_par_classe_jour = df_temp.groupby(['ID_Classe', 'Jour']).size()
    nb_surcharges = int((seances_par_classe_jour > 4).sum())
    penalite_surcharge = nb_surcharges * 1.0

    # 4. Sous-utilisation salles: -1.5 pts si taux < 40%
    df_temp['Taux_Remplissage'] = df_temp['Nb_Etudiants'] / df_temp['Capacite_Salle']
    nb_sous_util = int((df_temp['Taux_Remplissage'] < 0.4).sum())
    penalite_salles = nb_sous_util * 1.5

    penalite_totale = (
        penalite_trous_profs + penalite_trous_classes + penalite_surcharge + penalite_salles
    )
    max_penalite_tolerable = total_seances * 5.0

    score_final = max(0.0, 100.0 * (1 - (penalite_totale / max_penalite_tolerable)))
    score_final = round(score_final, 2)

    details = {
        'score_final': score_final,
        'penalite_trous_profs': penalite_trous_profs,
        'penalite_trous_classes': penalite_trous_classes,
        'penalite_surcharge': penalite_surcharge,
        'penalite_salles': penalite_salles,
        'nb_sous_util': nb_sous_util,
        'nb_surcharges': nb_surcharges,
        'total_seances': total_seances,
    }
    return score_final, details


def generer_n_variantes(
    df_enseignants: pd.DataFrame,
    df_salles: pd.DataFrame,
    df_matieres: pd.DataFrame,
    df_classes: pd.DataFrame,
    n_variantes: int = 10,
    max_retries: int = 300,
    base_seed: int = 42,
    progress_callback=None,
    heures_par_type: dict = None,
) -> List[Tuple[pd.DataFrame, float, dict]]:
    df_ens = df_enseignants.copy()
    for col in ['Matieres', 'Niveaux_Autorises', 'Creneaux_Indisponibles']:
        if col in df_ens.columns:
            df_ens[col] = df_ens[col].apply(safe_parse_list)

    if 'Heures_Max_Consecutives' not in df_ens.columns:
        df_ens['Heures_Max_Consecutives'] = 0

    matieres_par_type, matiere_info, salles_par_type, profs_par_matiere = build_indexes(
        df_ens, df_salles, df_matieres
    )

    resultats = []
    for i in range(1, n_variantes + 1):
        seed = base_seed + i
        df_emploi, df_echecs, stats = generer_emploi_du_temps(
            df_classes, matieres_par_type, matiere_info,
            salles_par_type, profs_par_matiere,
            seed=seed, max_retries=max_retries,
            heures_par_type=heures_par_type,
        )

        if len(df_emploi) > 0:
            score, details = calculer_score_emploi(df_emploi)
            df_emploi['Version'] = i
            df_emploi['Score'] = score
            resultats.append((df_emploi, score, details))

        if progress_callback:
            progress_callback(i / n_variantes)

    resultats.sort(key=lambda x: x[1], reverse=True)
    return resultats
