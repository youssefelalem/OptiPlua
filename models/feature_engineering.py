"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              OptiPlua — Feature Engineering Pipeline                        ║
║              models/feature_engineering.py                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Rôle   : Transformer les données brutes du simulateur en features          ║
║           numériques exploitables par le modèle XGBoost.                    ║
║                                                                              ║
║  Usage (entraînement) :                                                      ║
║      from models.feature_engineering import preprocess_data                 ║
║      X, y = preprocess_data(df, is_training=True)                           ║
║                                                                              ║
║  Usage (inférence Streamlit) :                                               ║
║      from models.feature_engineering import preprocess_data                 ║
║      X = preprocess_data(df_nouveau, is_training=False)                     ║
║                                                                              ║
║  Auteure : Douaa — Responsable ML, Projet OptiPlua © 2026                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import os
import warnings
import numpy as np
import pandas as pd
import joblib

from sklearn.preprocessing import LabelEncoder, MinMaxScaler

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION GLOBALE
# ─────────────────────────────────────────────────────────────────────────────

# Dossier où seront sauvegardés les encodeurs et le scaler
MODELS_DIR = os.path.join(os.path.dirname(__file__))

# Chemin du fichier regroupant tous les objets de prétraitement
ARTEFACTS_PATH = os.path.join(MODELS_DIR, "preprocessing_artefacts.joblib")

# Colonnes catégorielles à encoder avec LabelEncoder
COLS_CATEGORIQUES = [
    "Type_Etablissement",
    "Nom_Matiere",
    "Type_Salle",
    "Jour",
    "Niveau",        # ex : Licence, Master, Bac+2 …
    "ID_Classe",     # identifiant de groupe/classe
]

# Colonnes numériques à normaliser avec MinMaxScaler
COLS_NUMERIQUES = [
    "Nb_Etudiants",
    "Capacite_Salle",
    "Nb_Tentatives",
]

# Features dérivées calculées dans ce script (ne pas inclure dans COLS_NUMERIQUES
# car elles n'existent pas encore dans le CSV brut)
FEATURES_DERIVEES = [
    "Taux_Remplissage",       # Nb_Etudiants / Capacite_Salle
    "Heure_Debut_Num",        # Heure de début convertie en entier (ex : "08h30" → 8)
    "Est_Matin",              # 1 si le cours commence avant 12h, 0 sinon
    "Est_Debut_Semaine",      # 1 si Lundi ou Mardi
    "Pression_Planification", # log1p(Nb_Tentatives) — atténue les outliers
]

# Colonne cible
COL_CIBLE = "Score"

# Liste finale des features qui seront passées au modèle XGBoost
# (construite dynamiquement dans preprocess_data)
FEATURES_FINALES: list[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────

def _extraire_heure(serie: pd.Series) -> pd.Series:
    """
    Convertit une colonne d'heures au format string variable en entier.

    Formats acceptés :
        "08h30", "08:30", "8", "8h", "830", 8 (int), 8.5 (float)

    Retourne : Series d'entiers représentant l'heure (partie horaire uniquement).
    Exemple   : "13h45" → 13
    """
    def _parse(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip().lower()
        # Format "08h30" ou "8h"
        if "h" in val:
            return int(val.split("h")[0])
        # Format "08:30"
        if ":" in val:
            return int(val.split(":")[0])
        # Format numérique pur (int ou float)
        try:
            return int(float(val))
        except ValueError:
            return np.nan

    return serie.apply(_parse)


def _creer_features_derivees(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule et ajoute au DataFrame les colonnes dérivées définies dans
    FEATURES_DERIVEES.

    Paramètres
    ----------
    df : pd.DataFrame — données brutes

    Retourne
    --------
    df : pd.DataFrame — données enrichies (copie)
    """
    df = df.copy()

    # ── 1. Taux de Remplissage ────────────────────────────────────────────────
    # Mesure l'efficacité d'utilisation d'une salle.
    # Valeur proche de 1 : salle bien remplie (bon score attendu).
    # Valeur très faible : gaspillage de ressources (pénalité).
    # On évite la division par zéro avec np.where.
    df["Taux_Remplissage"] = np.where(
        df["Capacite_Salle"] > 0,
        df["Nb_Etudiants"] / df["Capacite_Salle"],
        0.0
    )

    # ── 2. Heure de Début Numérique ───────────────────────────────────────────
    # XGBoost ne peut pas traiter des chaînes comme "08h30" directement.
    # On extrait la partie entière de l'heure pour garder l'ordre chronologique.
    df["Heure_Debut_Num"] = _extraire_heure(df["Heure_Debut"])

    # ── 3. Est_Matin (feature binaire) ───────────────────────────────────────
    # Les cours du matin (avant 12h) ont souvent un meilleur taux de présence.
    # Cette feature binaire encode ce contexte temporel simplement.
    df["Est_Matin"] = (df["Heure_Debut_Num"] < 12).astype(int)

    # ── 4. Est_Debut_Semaine (feature binaire) ────────────────────────────────
    # Lundi et Mardi = début de semaine. Les emplois du temps sont souvent
    # plus chargés en début qu'en fin de semaine.
    df["Est_Debut_Semaine"] = df["Jour"].isin(["Lundi", "Mardi"]).astype(int)

    # ── 5. Pression de Planification ─────────────────────────────────────────
    # Nb_Tentatives mesure combien de fois le simulateur a essayé avant de
    # placer un cours. Une valeur élevée = planning sous contrainte forte.
    # On applique log1p pour atténuer l'effet des grandes valeurs aberrantes
    # (outliers) tout en préservant l'ordre relatif.
    df["Pression_Planification"] = np.log1p(df["Nb_Tentatives"])

    return df


def _encoder_colonnes(
    df: pd.DataFrame,
    encodeurs: dict,
    is_training: bool
) -> tuple[pd.DataFrame, dict]:
    """
    Applique un LabelEncoder à chaque colonne catégorielle présente dans le
    DataFrame.

    En mode entraînement (is_training=True) :
        - Crée et ajuste (fit) un LabelEncoder par colonne.
        - Stocke les encodeurs dans le dictionnaire `encodeurs`.

    En mode inférence (is_training=False) :
        - Réutilise les encodeurs déjà ajustés.
        - Gère les catégories inconnues en les remplaçant par -1.

    Paramètres
    ----------
    df          : DataFrame avec colonnes catégorielles brutes
    encodeurs   : dict {nom_colonne: LabelEncoder} (vide si is_training=True)
    is_training : bool

    Retourne
    --------
    df        : DataFrame avec colonnes encodées
    encodeurs : dict mis à jour
    """
    df = df.copy()

    for col in COLS_CATEGORIQUES:
        # Si la colonne n'existe pas dans le dataset, on l'ignore silencieusement
        if col not in df.columns:
            print(f"   [⚠️  Ignorée] Colonne '{col}' absente du DataFrame.")
            continue

        # Convertir en string pour uniformiser (évite les erreurs de type)
        df[col] = df[col].astype(str).fillna("INCONNU")

        if is_training:
            # Création et ajustement d'un nouvel encodeur
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encodeurs[col] = le
            print(f"   [✅ Encodé]  '{col}' → {len(le.classes_)} catégories uniques")

        else:
            # Récupération de l'encodeur sauvegardé lors de l'entraînement
            if col not in encodeurs:
                raise KeyError(
                    f"L'encodeur pour '{col}' est introuvable dans les artefacts. "
                    "Vérifiez que preprocess_data a été exécuté en mode is_training=True."
                )
            le = encodeurs[col]
            classes_connues = set(le.classes_)

            # Gestion des catégories inconnues (jamais vues à l'entraînement)
            # → on les remplace par la valeur la plus fréquente pour ne pas planter
            inconnus = set(df[col].unique()) - classes_connues
            if inconnus:
                print(f"   [⚠️  Inconnu] '{col}' : catégories {inconnus} remplacées par -1")
                df[col] = df[col].apply(
                    lambda x: le.transform([x])[0] if x in classes_connues else -1
                )
            else:
                df[col] = le.transform(df[col])

    return df, encodeurs


def _normaliser_colonnes(
    df: pd.DataFrame,
    scaler: MinMaxScaler | None,
    is_training: bool
) -> tuple[pd.DataFrame, MinMaxScaler]:
    """
    Normalise les colonnes numériques avec MinMaxScaler (plage [0, 1]).

    MinMaxScaler est préféré à StandardScaler ici car :
    - XGBoost est robuste à l'échelle, mais une normalisation cohérente aide
      l'inférence Streamlit à produire des résultats stables.
    - Les features comme Taux_Remplissage sont naturellement bornées [0, 1],
      ce qui est cohérent avec MinMaxScaler.

    Paramètres
    ----------
    df          : DataFrame avec colonnes numériques
    scaler      : MinMaxScaler existant (None si is_training=True)
    is_training : bool

    Retourne
    --------
    df     : DataFrame avec colonnes normalisées
    scaler : MinMaxScaler ajusté
    """
    df = df.copy()

    # Construire la liste des colonnes numériques réellement présentes
    cols_a_scaler = (
        [c for c in COLS_NUMERIQUES if c in df.columns] +
        [c for c in FEATURES_DERIVEES if c in df.columns]
    )

    if is_training:
        scaler = MinMaxScaler()
        df[cols_a_scaler] = scaler.fit_transform(df[cols_a_scaler])
        print(f"   [✅ Normalisé] {len(cols_a_scaler)} colonnes numériques (MinMaxScaler ajusté)")
    else:
        if scaler is None:
            raise ValueError(
                "Le scaler est None en mode inférence. "
                "Chargez d'abord les artefacts avec joblib.load()."
            )
        df[cols_a_scaler] = scaler.transform(df[cols_a_scaler])
        print(f"   [✅ Normalisé] {len(cols_a_scaler)} colonnes avec le scaler existant")

    return df, scaler


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

def preprocess_data(
    df: pd.DataFrame,
    is_training: bool = True
) -> pd.DataFrame | tuple[pd.DataFrame, pd.Series]:
    """
    Pipeline complet de Feature Engineering pour OptiPlua.

    Étapes réalisées :
        1. Validation et nettoyage minimal des données brutes
        2. Création des features dérivées (Taux_Remplissage, Est_Matin, etc.)
        3. Encodage des variables catégorielles (LabelEncoder)
        4. Normalisation des variables numériques (MinMaxScaler)
        5. Sélection des features finales (X)
        6. Séparation X / y (uniquement si COL_CIBLE présente)
        7. Sauvegarde ou chargement des artefacts (encodeurs + scaler)

    Paramètres
    ----------
    df          : pd.DataFrame
        Données brutes issues du simulateur (CSV de Youssef).
        Doit contenir au minimum les colonnes définies dans COLS_CATEGORIQUES
        et COLS_NUMERIQUES.

    is_training : bool, default=True
        True  → mode entraînement : ajuste et sauvegarde les encodeurs/scaler.
        False → mode inférence   : charge et réutilise les artefacts sauvegardés.

    Retourne
    --------
    Si la colonne 'Score' est présente ET is_training=True :
        (X, y) : tuple (pd.DataFrame, pd.Series)

    Sinon (inférence ou données sans score) :
        X : pd.DataFrame
    """
    global FEATURES_FINALES

    mode = "ENTRAÎNEMENT" if is_training else "INFÉRENCE"
    print("=" * 60)
    print(f"  OptiPlua — Feature Engineering — Mode : {mode}")
    print("=" * 60)
    print(f"  📊 Lignes reçues    : {len(df):,}")
    print(f"  📋 Colonnes reçues  : {list(df.columns)}")
    print("-" * 60)

    # ── ÉTAPE 0 : Copie défensive ─────────────────────────────────────────────
    # On ne modifie jamais le DataFrame original (bonne pratique Python)
    df = df.copy()

    # ── ÉTAPE 1 : Nettoyage minimal ───────────────────────────────────────────
    print("\n[1/6] Nettoyage des données…")

    nb_avant = len(df)
    df = df.dropna(subset=COLS_NUMERIQUES)   # Supprime les lignes sans valeur numérique
    nb_apres = len(df)
    if nb_avant != nb_apres:
        print(f"   → {nb_avant - nb_apres} lignes supprimées (valeurs nulles dans les numériques)")
    else:
        print(f"   ✅ Aucune ligne supprimée — données complètes")

    # ── ÉTAPE 2 : Features dérivées ───────────────────────────────────────────
    print("\n[2/6] Création des features dérivées…")
    df = _creer_features_derivees(df)
    for feat in FEATURES_DERIVEES:
        if feat in df.columns:
            print(f"   [✅ Créée]  '{feat}'")

    # ── ÉTAPE 3 : Chargement ou initialisation des artefacts ─────────────────
    print("\n[3/6] Gestion des artefacts (encodeurs & scaler)…")

    if is_training:
        # Mode entraînement : on part de zéro
        encodeurs: dict = {}
        scaler: MinMaxScaler | None = None
    else:
        # Mode inférence : on charge les artefacts sauvegardés
        if not os.path.exists(ARTEFACTS_PATH):
            raise FileNotFoundError(
                f"Artefacts introuvables : '{ARTEFACTS_PATH}'\n"
                "→ Lancez d'abord preprocess_data(df, is_training=True) pour les générer."
            )
        artefacts = joblib.load(ARTEFACTS_PATH)
        encodeurs = artefacts["encodeurs"]
        scaler    = artefacts["scaler"]
        print(f"   ✅ Artefacts chargés depuis : {ARTEFACTS_PATH}")

    # ── ÉTAPE 4 : Encodage des catégorielles ──────────────────────────────────
    print("\n[4/6] Encodage des variables catégorielles…")
    df, encodeurs = _encoder_colonnes(df, encodeurs, is_training)

    # ── ÉTAPE 5 : Normalisation des numériques ────────────────────────────────
    print("\n[5/6] Normalisation des variables numériques…")
    df, scaler = _normaliser_colonnes(df, scaler, is_training)

    # ── ÉTAPE 6 : Sélection des features finales ──────────────────────────────
    print("\n[6/6] Sélection des features finales…")

    # Construire la liste des colonnes à inclure dans X :
    # catégorielles encodées + numériques + features dérivées
    # On exclut : colonnes brutes inutiles (ID_Enseignant si non pertinent),
    #             la cible (Score), et Heure_Debut (remplacée par Heure_Debut_Num)
    cols_a_exclure = {
        COL_CIBLE,
        "Heure_Debut",     # Remplacée par Heure_Debut_Num (numérique)
        "ID_Enseignant",   # Identifiant trop granulaire → risque d'overfitting
    }

    FEATURES_FINALES = [
        col for col in df.columns
        if col not in cols_a_exclure
        and df[col].dtype in [np.float64, np.float32, np.int64, np.int32, float, int]
    ]

    print(f"   ✅ {len(FEATURES_FINALES)} features sélectionnées :")
    for f in FEATURES_FINALES:
        print(f"      • {f}")

    X = df[FEATURES_FINALES]

    # ── SAUVEGARDE des artefacts (uniquement en entraînement) ─────────────────
    if is_training:
        artefacts_a_sauvegarder = {
            "encodeurs"       : encodeurs,
            "scaler"          : scaler,
            "features_finales": FEATURES_FINALES,
        }
        joblib.dump(artefacts_a_sauvegarder, ARTEFACTS_PATH)
        print(f"\n   💾 Artefacts sauvegardés → {ARTEFACTS_PATH}")

    # ── SÉPARATION X / y ──────────────────────────────────────────────────────
    if COL_CIBLE in df.columns:
        y = df[COL_CIBLE].copy()
        print(f"\n   🎯 Variable cible (y) : '{COL_CIBLE}' | min={y.min():.1f}, max={y.max():.1f}, moy={y.mean():.2f}")
        print("=" * 60)
        print("  ✅ Feature Engineering terminé → Retourne (X, y)")
        print("=" * 60)
        return X, y

    else:
        print(f"\n   ℹ️  Colonne '{COL_CIBLE}' absente → mode inférence, retourne X uniquement.")
        print("=" * 60)
        print("  ✅ Feature Engineering terminé → Retourne X")
        print("=" * 60)
        return X


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION UTILITAIRE : Charger les features finales (pour train_model.py)
# ─────────────────────────────────────────────────────────────────────────────

def get_features_finales() -> list[str]:
    """
    Retourne la liste des noms de features utilisées lors de l'entraînement.

    Utile dans train_model.py pour s'assurer que le modèle et les données
    sont alignés sur les mêmes colonnes.

    Retourne
    --------
    list[str] : liste des noms de colonnes (features)

    Lève
    ----
    FileNotFoundError si les artefacts n'ont pas encore été générés.
    """
    if not os.path.exists(ARTEFACTS_PATH):
        raise FileNotFoundError(
            f"Artefacts non trouvés : '{ARTEFACTS_PATH}'\n"
            "→ Exécutez d'abord preprocess_data(df, is_training=True)."
        )
    artefacts = joblib.load(ARTEFACTS_PATH)
    return artefacts["features_finales"]


# ─────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE — Test rapide en exécution directe
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test d'intégration rapide :
        python models/feature_engineering.py

    Charge le CSV de test, applique le pipeline complet en mode entraînement,
    puis simule un passage en mode inférence sur un sous-ensemble.
    """
    import sys

    CHEMIN_TEST = os.path.join(
        os.path.dirname(__file__), "..", "data", "raw_schedules_test.csv"
    )

    print("\n" + "━" * 60)
    print("  TEST D'INTÉGRATION — feature_engineering.py")
    print("━" * 60)

    # ── Chargement du CSV ────────────────────────────────────────────────────
    try:
        df_raw = pd.read_csv(CHEMIN_TEST)
        print(f"\n  📁 CSV chargé : {CHEMIN_TEST} ({len(df_raw):,} lignes)")
    except FileNotFoundError:
        print(f"\n  ❌ Fichier introuvable : {CHEMIN_TEST}")
        print("  → Adaptez CHEMIN_TEST ou placez le CSV dans data/")
        sys.exit(1)

    # ── Simulation : ajout d'une colonne Score fictive ────────────────────────
    # (dans le vrai projet, Youssef fournit cette colonne dans le CSV)
    if "Score" not in df_raw.columns:
        print("\n  ℹ️  Colonne 'Score' absente → génération aléatoire pour le test")
        np.random.seed(42)
        df_raw["Score"] = np.random.uniform(50, 100, len(df_raw)).round(2)

    # ── Mode ENTRAÎNEMENT ────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("  ▶  TEST MODE : is_training=True")
    print("─" * 60)
    X_train, y_train = preprocess_data(df_raw, is_training=True)
    print(f"\n  Résultat → X shape : {X_train.shape} | y shape : {y_train.shape}")
    print(f"  Aperçu X :\n{X_train.head(3).to_string()}")

    # ── Mode INFÉRENCE ───────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("  ▶  TEST MODE : is_training=False (5 nouvelles lignes)")
    print("─" * 60)
    df_inference = df_raw.drop(columns=["Score"]).head(5)
    X_infer = preprocess_data(df_inference, is_training=False)
    print(f"\n  Résultat → X shape : {X_infer.shape}")
    print(f"  Aperçu X :\n{X_infer.to_string()}")

    print("\n  ✅ Tous les tests ont passé ! Le pipeline est opérationnel.")
    print("━" * 60 + "\n")
