"""
OptiPlua — Application Streamlit Professionnelle
Plateforme d'optimisation intelligente des emplois du temps scolaires.
Design: Premium Ed-Tech Intelligence (OptiPlus SaaS)
"""

import streamlit as st
import pandas as pd
import time
import json
import hashlib
import base64
from pathlib import Path
from simulator import generer_n_variantes, HEURES_PAR_TYPE, ALL_HEURES
from scorer import TimetableScorer

# ── Configuration ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OptiPlus - Optimisation Intelligente",
    page_icon="assets/favicon.ico" if Path("assets/favicon.ico").exists() else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

USERS_FILE = Path("data/users.json")
JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']
TYPES_ETABLISSEMENT = ['Ecole_Standard', 'Universite', 'Centre_Soutien']
TYPES_SALLE = ['Generale', 'Labo_Science', 'Labo_Informatique', 'Laboratoire', 'Amphitheatre']
MATIERES_DISPONIBLES = [
    'MATH', 'PHYSIQUE', 'CHIMIE', 'SVT', 'INFORMATIQUE',
    'FRANCAIS', 'ANGLAIS', 'ARABE', 'PHILOSOPHIE',
    'ECONOMIE', 'DROIT_CIVIL', 'BIOLOGIE',
    'ANALYSE', 'ALGEBRE', 'MECANIQUE_QUANTIQUE',
    'BASE_DE_DONNEES', 'RESEAUX',
    'HISTOIRE_GEO', 'EDUCATION_ISLAMIQUE', 'EDUCATION_ARTISTIQUE',
    'SPORT', 'LECTURE', 'ECRITURE', 'CALCUL',
]
NIVEAUX_DISPONIBLES = [
    # Ibtida2i (Primaire)
    '1ere_Annee_Primaire', '2eme_Annee_Primaire', '3eme_Annee_Primaire',
    '4eme_Annee_Primaire', '5eme_Annee_Primaire', '6eme_Annee_Primaire',
    # College (Iidadi)
    '1ere_Annee_College', '2eme_Annee_College', '3eme_Annee_College',
    # Lycee
    'Tronc_Commun', 'Baccalaureat',
    # Superieur
    'Prepa', 'Cycle_Ingenieur',
    'Licence_1', 'Licence_2', 'Licence_3',
    'Master_1', 'Master_2',
    # Centre Soutien
    'Soutien_Primaire', 'Soutien_College', 'Soutien_Lycee',
]

# ── Logo ─────────────────────────────────────────────────────────────────────
LOGO_PATH = Path("logo/without bg.svg")
LOGO_B64 = ""
if LOGO_PATH.exists():
    LOGO_B64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()


def _logo_img(size: int = 36) -> str:
    """Return an <img> tag for the logo, or a gradient icon fallback."""
    if LOGO_B64:
        return f'<img src="data:image/svg+xml;base64,{LOGO_B64}" style="width:{size}px; height:{size}px; border-radius:8px; object-fit:contain;" />'
    return f'''<div style="width:{size}px; height:{size}px; background:linear-gradient(135deg,#1D4ED8,#06B6D4); border-radius:8px; display:flex; align-items:center; justify-content:center; color:white;">
        <span class="material-symbols-outlined" style="font-variation-settings:\'FILL\' 1; font-size:{int(size*0.5)}px;">auto_awesome</span>
    </div>'''


# ── CSS Premium OptiPlus Design System ──────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    :root {
        --bg-deepest: #0B1220;
        --bg-surface: #111A2E;
        --bg-surface-high: #17213A;
        --bg-input: #0B1220;
        --border: #26324D;
        --border-light: rgba(38, 50, 77, 0.5);
        --primary: #b7c4ff;
        --primary-container: #1D4ED8;
        --secondary: #4cd7f6;
        --secondary-container: #03b5d3;
        --on-surface: #e0e3e5;
        --on-surface-variant: #c4c5d7;
        --outline: #8e90a0;
        --outline-variant: #434655;
        --error: #ffb4ab;
        --error-container: #93000a;
        --surface-container-highest: #323537;
        --surface-container-low: #191c1e;
        --tertiary: #a4c9ff;
        --glass-bg: rgba(17, 26, 46, 0.8);
    }

    .stApp {
        background: var(--bg-deepest);
        font-family: 'Inter', -apple-system, sans-serif;
        color: var(--on-surface);
    }

    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    div[data-testid="stDecoration"] {display: none;}

    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined';
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        display: inline-block;
        line-height: 1;
        vertical-align: middle;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-deepest); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--outline-variant); }

    /* ── Auth Page ── */
    .auth-shell {
        display: grid;
        grid-template-columns: 1fr 1fr;
        max-width: 1100px;
        margin: 0 auto;
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 24px 80px rgba(0,0,0,0.5);
        min-height: 600px;
    }
    .auth-brand {
        position: relative;
        padding: 3rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border-right: 1px solid var(--outline-variant);
        overflow: hidden;
    }
    .auth-brand::before {
        content: '';
        position: absolute;
        top: -20%; left: -10%;
        width: 60%; height: 60%;
        background: rgba(29, 78, 216, 0.15);
        border-radius: 50%;
        filter: blur(100px);
    }
    .auth-brand-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 3rem;
        position: relative;
        z-index: 1;
    }
    .auth-brand-icon {
        width: 40px; height: 40px;
        background: linear-gradient(135deg, #1D4ED8, #06B6D4);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        box-shadow: 0 4px 12px rgba(29, 78, 216, 0.4);
    }
    .auth-brand-name {
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--primary);
        letter-spacing: -0.5px;
    }
    .auth-brand h1 {
        font-size: 2.8rem;
        font-weight: 700;
        line-height: 1.15;
        color: var(--on-surface);
        position: relative;
        z-index: 1;
        margin-bottom: 1rem;
    }
    .auth-brand h1 span { color: var(--secondary); }
    .auth-brand p {
        color: var(--on-surface-variant);
        font-size: 1rem;
        line-height: 1.6;
        max-width: 400px;
        position: relative;
        z-index: 1;
    }
    .auth-testimonial {
        background: rgba(39, 42, 44, 0.5);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--outline-variant);
        position: relative;
        z-index: 1;
    }
    .auth-testimonial .stars {
        color: var(--secondary);
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .auth-testimonial .quote {
        font-style: italic;
        color: var(--on-surface-variant);
        font-size: 0.85rem;
        line-height: 1.5;
    }
    .auth-testimonial .author {
        margin-top: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--on-surface);
        text-transform: uppercase;
    }
    .auth-testimonial .role {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        color: var(--on-surface-variant);
        text-transform: none;
        letter-spacing: normal;
    }
    .auth-form-side {
        padding: 3rem;
        background: #0b0f10;
        display: flex;
        flex-direction: column;
    }

    /* ── Top App Bar ── */
    .top-app-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
    }
    .top-app-bar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .top-app-bar-icon {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #1D4ED8, #06B6D4);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
    }
    .top-app-bar-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: var(--primary);
        letter-spacing: -0.5px;
    }
    .top-app-bar-subtitle {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--on-surface-variant);
        opacity: 0.7;
        text-transform: uppercase;
    }
    .top-app-bar-user {
        display: flex;
        align-items: center;
        gap: 1rem;
        color: var(--on-surface-variant);
        font-size: 0.85rem;
    }
    .top-app-bar-user .user-name {
        color: var(--on-surface);
        font-weight: 600;
    }
    .top-app-bar-user .user-school {
        font-size: 0.7rem;
        color: var(--secondary);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* ── Sidebar Nav (simulated with tabs) ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-surface);
        border-radius: 12px;
        padding: 6px;
        border: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: var(--on-surface-variant);
        font-weight: 500;
        padding: 0.7rem 1.5rem;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: var(--primary-container) !important;
        color: #cad3ff !important;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ── Page Header ── */
    .page-header {
        margin-bottom: 2rem;
    }
    .page-header-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--secondary);
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .page-header h2 {
        font-size: 2rem;
        font-weight: 600;
        color: var(--on-surface);
        letter-spacing: -0.01em;
        margin: 0;
    }
    .page-header p {
        color: var(--on-surface-variant);
        font-size: 1rem;
        margin: 0.25rem 0 0 0;
    }

    /* ── Glass Panel ── */
    .glass-panel {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    /* ── Stats Cards ── */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: var(--surface-container-low);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--outline-variant);
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .stat-card-icon {
        width: 48px; height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
    }
    .stat-card-icon.teachers { background: rgba(29,78,216,0.15); color: var(--primary); }
    .stat-card-icon.students { background: rgba(3,181,211,0.15); color: var(--secondary); }
    .stat-card-icon.rooms { background: rgba(0,93,168,0.15); color: var(--tertiary); }
    .stat-card-icon.conflicts { background: rgba(147,0,10,0.15); color: var(--error); }
    .stat-card-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--on-surface-variant);
        text-transform: uppercase;
    }
    .stat-card-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--on-surface);
    }

    /* ── Workspace Tabs (inside cards) ── */
    .workspace-tabs {
        display: flex;
        border-bottom: 1px solid var(--outline-variant);
        background: rgba(16,20,21,0.5);
        margin: -1.5rem -1.5rem 1.5rem -1.5rem;
        border-radius: 16px 16px 0 0;
        overflow: hidden;
    }
    .workspace-tab {
        padding: 1rem 2rem;
        font-size: 1rem;
        font-weight: 500;
        color: var(--on-surface-variant);
        border-bottom: 2px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
    }
    .workspace-tab.active {
        color: var(--primary);
        border-bottom-color: var(--primary);
        background: rgba(29, 78, 216, 0.05);
    }

    /* ── Form Styling ── */
    .form-section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--on-surface);
        margin-bottom: 1rem;
    }
    .form-section-title .material-symbols-outlined {
        color: var(--secondary);
    }
    .label-caps {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--on-surface-variant);
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: var(--bg-input) !important;
        border: 1px solid var(--outline-variant) !important;
        border-radius: 8px !important;
        color: var(--on-surface) !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: var(--primary-container);
        color: #cad3ff;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 700;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        filter: brightness(1.1);
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(29, 78, 216, 0.3);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1D4ED8 0%, #06B6D4 100%);
        color: white;
        font-size: 1rem;
        padding: 1rem 2rem;
        box-shadow: 0 8px 24px rgba(29, 78, 216, 0.4);
    }
    .stButton > button[kind="primary"]:hover {
        transform: scale(1.01) translateY(-1px);
        box-shadow: 0 12px 32px rgba(29, 78, 216, 0.5);
    }

    /* ── Download Button ── */
    .stDownloadButton > button {
        background: transparent;
        border: 1px solid var(--border);
        color: var(--on-surface-variant);
        border-radius: 8px;
        font-weight: 700;
    }
    .stDownloadButton > button:hover {
        background: var(--secondary);
        color: #003640;
        border-color: var(--secondary);
    }

    /* ── Progress Bar ── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--primary-container), var(--secondary));
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: var(--surface-container-low) !important;
        border-radius: 12px !important;
        border: 1px solid var(--outline-variant) !important;
        color: var(--on-surface) !important;
    }
    details[data-testid="stExpander"] {
        background: var(--surface-container-low);
        border: 1px solid var(--outline-variant);
        border-radius: 12px;
    }

    /* ── Dataframe ── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--outline-variant);
    }

    /* ── Top 3 Result Cards ── */
    .result-card {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .result-card-1 { border-top: 4px solid var(--secondary); }
    .result-card-2 { border-top: 4px solid rgba(183, 196, 255, 0.5); }
    .result-card-3 { border-top: 4px solid var(--outline-variant); }
    .result-card::after {
        content: '';
        position: absolute;
        top: -20px; right: -20px;
        width: 80px; height: 80px;
        border-radius: 50%;
        filter: blur(40px);
        opacity: 0.08;
        transition: opacity 0.3s;
    }
    .result-card:hover::after { opacity: 0.15; }
    .result-card-1::after { background: var(--secondary); }
    .result-card-2::after { background: var(--primary); }
    .result-card-3::after { background: var(--outline); }

    .result-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .result-badge-1 {
        background: rgba(3, 181, 211, 0.15);
        color: var(--secondary);
        border: 1px solid rgba(76, 215, 246, 0.3);
    }
    .result-badge-2 {
        background: rgba(29, 78, 216, 0.15);
        color: var(--primary);
        border: 1px solid rgba(183, 196, 255, 0.3);
    }
    .result-badge-3 {
        background: rgba(50, 53, 55, 0.5);
        color: var(--on-surface-variant);
        border: 1px solid var(--outline-variant);
    }

    .result-score {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 1rem;
    }
    .result-score-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--on-surface);
    }
    .result-score-max {
        font-size: 0.85rem;
        color: var(--outline);
        opacity: 0.6;
    }
    .result-score-1 .result-score-value { color: var(--secondary); }

    .result-detail-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0;
        border-bottom: 1px solid rgba(67, 70, 85, 0.3);
    }
    .result-detail-row:last-child { border: none; }
    .result-detail-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--on-surface-variant);
        text-transform: uppercase;
    }
    .result-detail-value {
        font-size: 1rem;
        font-weight: 700;
        color: var(--on-surface);
    }

    /* ── Config Panel (Generation) ── */
    .config-panel {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
    }
    .config-title {
        font-size: 1.1rem;
        font-weight: 500;
        color: var(--on-surface);
        margin-bottom: 0.25rem;
    }
    .config-desc {
        font-size: 0.75rem;
        color: var(--on-surface-variant);
    }
    .config-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary);
    }

    /* ── Scoring Radio Cards ── */
    .scoring-card {
        background: var(--surface-container-low);
        border: 1px solid var(--outline-variant);
        border-radius: 12px;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .scoring-card:hover {
        background: var(--bg-surface-high);
    }
    .scoring-card.active {
        border-color: var(--primary);
        background: rgba(29, 78, 216, 0.05);
    }
    .scoring-card-title {
        font-weight: 700;
        color: var(--on-surface);
        margin-bottom: 0.25rem;
    }
    .scoring-card-desc {
        font-size: 0.75rem;
        color: var(--on-surface-variant);
    }

    /* ── Progress Live Panel ── */
    .live-progress-panel {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
    }

    /* ── Input Summary ── */
    .input-summary-item {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .input-summary-icon {
        width: 40px; height: 40px;
        border-radius: 8px;
        background: var(--surface-container-highest);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .input-summary-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--outline);
        text-transform: uppercase;
    }
    .input-summary-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--on-surface);
    }

    /* ── Ready Badge ── */
    .ready-badge {
        background: rgba(29, 78, 216, 0.1);
        border: 1px solid rgba(29, 78, 216, 0.2);
        border-radius: 12px;
        padding: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-top: 1.5rem;
    }
    .ready-badge-icon { color: var(--primary); }
    .ready-badge-title {
        font-weight: 700;
        color: var(--primary);
        font-size: 0.9rem;
    }
    .ready-badge-desc {
        font-size: 0.75rem;
        color: var(--on-surface-variant);
    }

    /* ── Full Ranking Table ── */
    .ranking-table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
    }
    .ranking-table thead {
        background: rgba(16,20,21,0.5);
    }
    .ranking-table th {
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--on-surface-variant);
        text-transform: uppercase;
        border-bottom: 1px solid var(--outline-variant);
    }
    .ranking-table td {
        padding: 1rem;
        border-bottom: 1px solid rgba(67, 70, 85, 0.3);
        color: var(--on-surface);
    }
    .ranking-table tr:hover {
        background: rgba(39, 42, 44, 0.5);
    }
    .ranking-bar {
        width: 100px;
        height: 6px;
        background: var(--surface-container-highest);
        border-radius: 9999px;
        overflow: hidden;
    }
    .ranking-bar-fill {
        height: 100%;
        border-radius: 9999px;
    }

    /* ── Timetable Visual Grid ── */
    .tt-visual {
        width: 100%;
        border-collapse: separate;
        border-spacing: 4px;
    }
    .tt-visual th {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: var(--on-surface-variant);
        padding: 0.5rem;
        text-align: center;
    }
    .tt-visual td {
        padding: 0;
        vertical-align: top;
    }
    .tt-cell {
        min-height: 52px;
        padding: 0.4rem 0.6rem;
        border-radius: 8px;
        border-left: 3px solid;
        font-size: 0.7rem;
    }
    .tt-cell-filled {
        background: rgba(29,78,216,0.1);
        border-color: var(--primary-container);
    }
    .tt-cell-filled .tt-subj {
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 1px;
    }
    .tt-cell-filled .tt-prof {
        color: var(--on-surface-variant);
        font-size: 0.6rem;
    }
    .tt-cell-filled .tt-room {
        color: var(--secondary);
        font-size: 0.55rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .tt-cell-empty {
        background: rgba(38,50,77,0.15);
        border-color: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--outline-variant);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.55rem;
        letter-spacing: 0.05em;
    }
    /* color variations for subjects */
    .tt-cell-v1 { border-color: #1D4ED8; background: rgba(29,78,216,0.1); }
    .tt-cell-v1 .tt-subj { color: #93b4ff; }
    .tt-cell-v2 { border-color: #06B6D4; background: rgba(6,182,212,0.1); }
    .tt-cell-v2 .tt-subj { color: #4cd7f6; }
    .tt-cell-v3 { border-color: #8B5CF6; background: rgba(139,92,246,0.1); }
    .tt-cell-v3 .tt-subj { color: #c4b5fd; }
    .tt-cell-v4 { border-color: #10B981; background: rgba(16,185,129,0.1); }
    .tt-cell-v4 .tt-subj { color: #6ee7b7; }
    .tt-cell-v5 { border-color: #F59E0B; background: rgba(245,158,11,0.1); }
    .tt-cell-v5 .tt-subj { color: #fcd34d; }
    .tt-cell-v6 { border-color: #EF4444; background: rgba(239,68,68,0.1); }
    .tt-cell-v6 .tt-subj { color: #fca5a5; }

    /* ── Edit / Delete Buttons ── */
    .action-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px; height: 28px;
        border-radius: 6px;
        border: 1px solid var(--outline-variant);
        background: transparent;
        color: var(--on-surface-variant);
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.8rem;
    }
    .action-btn:hover {
        background: var(--bg-surface-high);
        color: var(--on-surface);
    }
    .action-btn-delete:hover {
        background: rgba(147,0,10,0.15);
        color: var(--error);
        border-color: rgba(255,180,171,0.3);
    }

    /* ── CTA Section ── */
    .cta-section {
        background: linear-gradient(135deg, var(--surface-container-low), var(--bg-surface-high));
        border: 1px solid var(--outline-variant);
        border-radius: 16px;
        padding: 2rem;
        position: relative;
        overflow: hidden;
    }
    .cta-section h3 {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--on-surface);
        margin-bottom: 0.5rem;
    }
    .cta-section p {
        color: var(--on-surface-variant);
        max-width: 500px;
        margin-bottom: 1.5rem;
    }

    /* ── Insights Row ── */
    .insights-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
    }
    .insight-card {
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(67, 70, 85, 0.3);
        display: flex;
        gap: 1rem;
    }
    .insight-card p {
        font-size: 0.9rem;
        color: var(--on-surface-variant);
        margin: 0;
    }
    .insight-card span.val {
        color: var(--on-surface);
        font-weight: 700;
    }

    /* ── Form Submit Button Override ── */
    [data-testid="stFormSubmitButton"] > button,
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #1D4ED8 0%, #06B6D4 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover,
    .stFormSubmitButton > button:hover {
        filter: brightness(1.1) !important;
        box-shadow: 0 8px 24px rgba(29, 78, 216, 0.4) !important;
    }
    .stButton > button[kind="primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #1D4ED8 0%, #06B6D4 100%) !important;
        color: white !important;
    }

    /* ── Slider fix ── */
    .stSlider > div > div > div {
        background: var(--outline-variant) !important;
    }
    .stSlider > div > div > div > div {
        background: var(--primary-container) !important;
    }

    /* ── Radio ── */
    .stRadio > div {
        gap: 0.5rem;
    }

    /* ── Checkbox ── */
    .stCheckbox > label > span {
        color: var(--on-surface-variant) !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ── User Authentication ──────────────────────────────────────────────────────
def load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text(encoding='utf-8'))
    return {}


def save_users(users: dict):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding='utf-8')


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def render_auth_page():
    st.markdown("""
    <div style="position:fixed; inset:0; overflow:hidden; pointer-events:none; z-index:-1;">
        <div style="position:absolute; top:-20%; left:-10%; width:50%; height:50%; border-radius:50%; background:rgba(29,78,216,0.1); filter:blur(120px);"></div>
        <div style="position:absolute; bottom:-20%; right:-10%; width:50%; height:50%; border-radius:50%; background:rgba(76,215,246,0.1); filter:blur(120px);"></div>
    </div>
    """, unsafe_allow_html=True)

    col_spacer1, col_brand, col_form, col_spacer2 = st.columns([0.5, 3, 3, 0.5])

    with col_brand:
        logo_html = _logo_img(40)
        st.markdown(f"""
        <div style="padding:2rem 0;">
            <div class="auth-brand-logo">
                {logo_html}
                <span class="auth-brand-name">OptiPlus</span>
            </div>
            <h1 style="font-size:2.8rem; font-weight:700; line-height:1.15; color:#e0e3e5; margin:0 0 1rem 0;">
                Intelligence pour une Education <span style="color:#4cd7f6;">Optimale</span>.
            </h1>
            <p style="color:#c4c5d7; font-size:1rem; line-height:1.6; max-width:400px;">
                Optimisez les emplois du temps de votre etablissement avec notre moteur d'intelligence artificielle et d'optimisation heuristique avancee.
            </p>
            <div style="margin-top:3rem;">
                <div class="auth-testimonial">
                    <div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
                    <div class="quote">
                        "OptiPlus a reduit notre temps de planification de trois semaines a quatre heures."
                    </div>
                    <div class="author" style="margin-top:1rem;">Dr. Sarah Jensen</div>
                    <div class="role">Directrice Academique, Stellar Academy</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        st.markdown('<div style="padding:1rem 0;">', unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["CONNEXION", "INSCRIPTION"])

        with tab_login:
            st.markdown('<p class="label-caps" style="margin-top:1rem;">ADRESSE EMAIL</p>', unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="admin@ecole.edu", label_visibility="collapsed")
                st.markdown('<p class="label-caps">MOT DE PASSE</p>', unsafe_allow_html=True)
                password = st.text_input("Mot de passe", type="password", placeholder="........", label_visibility="collapsed")
                submit = st.form_submit_button("Se connecter au portail", use_container_width=True, type="primary")

                if submit:
                    if not email or not password:
                        st.error("Veuillez remplir tous les champs.")
                    else:
                        users = load_users()
                        hashed = hash_password(password)
                        if email in users and users[email]['password'] == hashed:
                            st.session_state['authenticated'] = True
                            st.session_state['user_email'] = email
                            st.session_state['user_name'] = users[email].get('name', email)
                            st.session_state['user_school'] = users[email].get('school', '')
                            st.rerun()
                        else:
                            st.error("Email ou mot de passe incorrect.")

        with tab_signup:
            with st.form("signup_form"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<p class="label-caps">NOM COMPLET</p>', unsafe_allow_html=True)
                    name = st.text_input("Nom", placeholder="Ahmed Benali", label_visibility="collapsed")
                with c2:
                    st.markdown('<p class="label-caps">NOM DE L\'ETABLISSEMENT</p>', unsafe_allow_html=True)
                    school = st.text_input("Ecole", placeholder="Lycee Excellence", label_visibility="collapsed")

                st.markdown('<p class="label-caps">EMAIL PROFESSIONNEL</p>', unsafe_allow_html=True)
                new_email = st.text_input("Email", placeholder="admin@ecole.edu", key="signup_email", label_visibility="collapsed")
                st.markdown('<p class="label-caps">MOT DE PASSE</p>', unsafe_allow_html=True)
                new_password = st.text_input("Mot de passe", type="password", placeholder="Min. 6 caracteres", key="signup_pass", label_visibility="collapsed")
                st.markdown('<p class="label-caps">CONFIRMER LE MOT DE PASSE</p>', unsafe_allow_html=True)
                confirm_password = st.text_input("Confirmer", type="password", placeholder="........", label_visibility="collapsed")
                submit_signup = st.form_submit_button("Creer le compte administrateur", use_container_width=True, type="primary")

                if submit_signup:
                    if not all([name, school, new_email, new_password, confirm_password]):
                        st.error("Veuillez remplir tous les champs.")
                    elif new_password != confirm_password:
                        st.error("Les mots de passe ne correspondent pas.")
                    elif len(new_password) < 6:
                        st.error("Le mot de passe doit contenir au moins 6 caracteres.")
                    else:
                        users = load_users()
                        if new_email in users:
                            st.error("Cet email est deja utilise.")
                        else:
                            users[new_email] = {
                                'name': name,
                                'school': school,
                                'password': hash_password(new_password),
                            }
                            save_users(users)
                            st.success("Compte cree avec succes ! Connectez-vous maintenant.")

        st.markdown('</div>', unsafe_allow_html=True)


# ── Top App Bar ─────────────────────────────────────────────────────────────
def render_navbar():
    col1, col2, col3 = st.columns([4, 4, 2])
    with col1:
        logo_html = _logo_img(36)
        st.markdown(f"""
        <div class="top-app-bar-brand">
            {logo_html}
            <div>
                <div class="top-app-bar-title">OptiPlus</div>
                <div class="top-app-bar-subtitle">Admin Portal</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        school_name = st.session_state.get('user_school', '')
        if school_name:
            st.markdown(f"""
            <div style="text-align:center; padding-top:0.5rem;">
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; font-weight:600; letter-spacing:0.05em; color:var(--on-surface-variant); text-transform:uppercase;">Etablissement</span>
                <br>
                <span style="color:var(--on-surface); font-weight:600; font-size:0.95rem;">{school_name}</span>
            </div>
            """, unsafe_allow_html=True)
    with col3:
        c_user, c_logout = st.columns([3, 2])
        with c_user:
            user_name = st.session_state.get('user_name', '')
            st.markdown(f"""
            <div style="text-align:right; padding-top:0.3rem;">
                <span style="color:var(--on-surface); font-size:0.9rem; font-weight:600;">{user_name}</span>
            </div>
            """, unsafe_allow_html=True)
        with c_logout:
            if st.button("Logout", key="logout_btn"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    st.markdown('<div style="border-bottom:1px solid #26324D; margin:0.5rem 0 1.5rem 0;"></div>', unsafe_allow_html=True)


# ── Data Input Page ──────────────────────────────────────────────────────────
def render_data_page():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-status">
            <span class="material-symbols-outlined" style="font-size:1rem; vertical-align:middle;">edit_note</span>
            Espace de travail
        </div>
        <h2>Saisie des Donnees</h2>
        <p>Definissez les elements structurels pour votre prochain cycle d'optimisation.</p>
    </div>
    """, unsafe_allow_html=True)

    input_method = st.radio(
        "Methode de saisie",
        ["Formulaire interactif", "Importer des fichiers CSV", "Donnees d'exemple"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown(f"""
    <div style="display:flex; border-bottom:1px solid var(--outline-variant); margin-bottom:1.5rem;">
        <div class="workspace-tab {'active' if input_method == 'Formulaire interactif' else ''}">Formulaire Interactif</div>
        <div class="workspace-tab {'active' if input_method == 'Importer des fichiers CSV' else ''}">Import CSV</div>
        <div class="workspace-tab {'active' if input_method == "Donnees d'exemple" else ''}">Donnees d'Exemple</div>
    </div>
    """, unsafe_allow_html=True)

    if input_method == "Donnees d'exemple":
        _load_sample_data()
    elif input_method == "Importer des fichiers CSV":
        _load_csv_data()
    else:
        _load_form_data()


def _load_sample_data():
    data_dir = Path('data')
    try:
        df_ens_all = pd.read_csv(data_dir / 'enseignants_data.csv')
        df_sal_all = pd.read_csv(data_dir / 'salles_data.csv')
        df_mat_all = pd.read_csv(data_dir / 'matieres_data.csv')
        df_cls_all = pd.read_csv(data_dir / 'classes_data.csv')

        available_types = sorted(df_cls_all['Type_Etablissement'].unique())
        type_labels = {t: t.replace('_', ' ') for t in available_types}

        st.markdown('<p class="label-caps">TYPE D\'ETABLISSEMENT</p>', unsafe_allow_html=True)
        selected_type = st.selectbox(
            "Type d'etablissement",
            available_types,
            format_func=lambda x: type_labels[x],
            label_visibility="collapsed",
        )

        df_ens = df_ens_all[df_ens_all['Type_Etablissement'] == selected_type].reset_index(drop=True)
        df_sal = df_sal_all[df_sal_all['Type_Etablissement'] == selected_type].reset_index(drop=True)
        df_mat = df_mat_all[df_mat_all['Type_Etablissement'] == selected_type].reset_index(drop=True)
        df_cls = df_cls_all[df_cls_all['Type_Etablissement'] == selected_type].reset_index(drop=True)

        _show_data_stats(df_ens, df_sal, df_mat, df_cls)
        _store_data(df_ens, df_sal, df_mat, df_cls)

        with st.expander("Apercu des donnees"):
            t1, t2, t3, t4 = st.tabs(["Enseignants", "Salles", "Matieres", "Classes"])
            with t1: st.dataframe(df_ens.head(10), use_container_width=True)
            with t2: st.dataframe(df_sal.head(10), use_container_width=True)
            with t3: st.dataframe(df_mat.head(10), use_container_width=True)
            with t4: st.dataframe(df_cls.head(10), use_container_width=True)

        _show_cta_section()

    except FileNotFoundError:
        st.error("Fichiers d'exemple introuvables dans le dossier data/")


def _load_csv_data():
    st.markdown("""
    <div class="form-section-title">
        <span class="material-symbols-outlined">upload_file</span>
        Importez vos 4 fichiers CSV
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        f_ens = st.file_uploader("Enseignants", type=['csv'], key='csv_ens')
        f_mat = st.file_uploader("Matieres", type=['csv'], key='csv_mat')
    with col2:
        f_sal = st.file_uploader("Salles", type=['csv'], key='csv_sal')
        f_cls = st.file_uploader("Classes", type=['csv'], key='csv_cls')

    if all([f_ens, f_sal, f_mat, f_cls]):
        df_ens = pd.read_csv(f_ens)
        df_sal = pd.read_csv(f_sal)
        df_mat = pd.read_csv(f_mat)
        df_cls = pd.read_csv(f_cls)

        errors = _validate_all(df_ens, df_sal, df_mat, df_cls)
        if errors:
            for e in errors:
                st.error(e)
            return

        all_types = sorted(set(df_cls['Type_Etablissement'].unique()))
        if len(all_types) > 1:
            selected_type = st.selectbox(
                "Vos fichiers contiennent plusieurs types. Selectionnez celui de votre etablissement :",
                all_types,
                format_func=lambda x: x.replace('_', ' '),
            )
            df_ens = df_ens[df_ens['Type_Etablissement'] == selected_type].reset_index(drop=True)
            df_sal = df_sal[df_sal['Type_Etablissement'] == selected_type].reset_index(drop=True)
            df_mat = df_mat[df_mat['Type_Etablissement'] == selected_type].reset_index(drop=True)
            df_cls = df_cls[df_cls['Type_Etablissement'] == selected_type].reset_index(drop=True)

        _show_data_stats(df_ens, df_sal, df_mat, df_cls)
        _store_data(df_ens, df_sal, df_mat, df_cls)
    else:
        st.info("Veuillez charger les 4 fichiers CSV pour continuer.")


def _load_form_data():
    if 'form_teachers' not in st.session_state:
        st.session_state['form_teachers'] = []
    if 'form_rooms' not in st.session_state:
        st.session_state['form_rooms'] = []
    if 'form_subjects' not in st.session_state:
        st.session_state['form_subjects'] = []
    if 'form_classes' not in st.session_state:
        st.session_state['form_classes'] = []

    st.markdown('<p class="label-caps">TYPE D\'ETABLISSEMENT</p>', unsafe_allow_html=True)
    type_etab = st.selectbox(
        "Type d'etablissement",
        TYPES_ETABLISSEMENT,
        format_func=lambda x: x.replace('_', ' '),
        label_visibility="collapsed",
    )
    st.session_state['form_type_etab'] = type_etab

    tab_ens, tab_sal, tab_mat, tab_cls = st.tabs([
        "Enseignants", "Salles", "Matieres", "Classes",
    ])

    with tab_ens:
        _form_teachers(type_etab)
    with tab_sal:
        _form_rooms(type_etab)
    with tab_mat:
        _form_subjects(type_etab)
    with tab_cls:
        _form_classes(type_etab)

    st.markdown('<div style="margin:1.5rem 0;"></div>', unsafe_allow_html=True)
    if st.button("Valider et continuer", type="primary", use_container_width=True):
        teachers = st.session_state.get('form_teachers', [])
        rooms = st.session_state.get('form_rooms', [])
        subjects = st.session_state.get('form_subjects', [])
        classes = st.session_state.get('form_classes', [])

        if not teachers or not rooms or not subjects or not classes:
            st.error("Veuillez ajouter au moins 1 enseignant, 1 salle, 1 matiere et 1 classe.")
            return

        df_ens = pd.DataFrame(teachers)
        df_sal = pd.DataFrame(rooms)
        df_mat = pd.DataFrame(subjects)
        df_cls = pd.DataFrame(classes)
        _store_data(df_ens, df_sal, df_mat, df_cls)
        _show_data_stats(df_ens, df_sal, df_mat, df_cls)


def _get_creneaux_for_type(type_etab: str) -> list:
    """Return available time slots for this school type."""
    heures = HEURES_PAR_TYPE.get(type_etab, ALL_HEURES)
    return [f"{j}_{h}" for j in JOURS for h in heures]


def _form_teachers(type_etab: str):
    st.markdown("""
    <div class="form-section-title">
        <span class="material-symbols-outlined">group</span>
        Ajouter un enseignant
    </div>
    """, unsafe_allow_html=True)
    with st.form("add_teacher_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<p class="label-caps">NOM COMPLET</p>', unsafe_allow_html=True)
            t_name = st.text_input("Nom", placeholder="Ex: Prof. Ahmed BENALI", label_visibility="collapsed")
            st.markdown('<p class="label-caps">MATIERES ENSEIGNEES</p>', unsafe_allow_html=True)
            t_matieres = st.multiselect("Matieres", MATIERES_DISPONIBLES, label_visibility="collapsed")
            st.markdown('<p class="label-caps">HEURES MAX / SEMAINE</p>', unsafe_allow_html=True)
            t_max_h = st.number_input("Heures max", min_value=1, max_value=40, value=18, step=1, label_visibility="collapsed")
        with c2:
            st.markdown('<p class="label-caps">NIVEAUX AUTORISES</p>', unsafe_allow_html=True)
            t_niveaux = st.multiselect("Niveaux", NIVEAUX_DISPONIBLES, label_visibility="collapsed")
            st.markdown('<p class="label-caps">HEURES MAX CONSECUTIVES</p>', unsafe_allow_html=True)
            t_max_consec = st.number_input("Consecutives", min_value=1, max_value=8, value=4, step=1, label_visibility="collapsed")
            st.markdown('<p class="label-caps">INDICE DE FLEXIBILITE</p>', unsafe_allow_html=True)
            t_flex = st.slider("Flexibilite", 0.0, 1.0, 0.5, label_visibility="collapsed")
        st.markdown('<p class="label-caps">CRENEAUX INDISPONIBLES</p>', unsafe_allow_html=True)
        creneaux_list = _get_creneaux_for_type(type_etab)
        t_indispo = st.multiselect(
            "Indisponibilites",
            creneaux_list,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Ajouter l'enseignant", use_container_width=True)
        if submitted:
            if not t_name or not t_matieres or not t_niveaux:
                st.error("Nom, matieres et niveaux sont obligatoires.")
            else:
                idx = len(st.session_state['form_teachers']) + 1
                st.session_state['form_teachers'].append({
                    'ID_Enseignant': f'ENS_{idx:03d}',
                    'Nom_Enseignant': t_name,
                    'Type_Etablissement': type_etab,
                    'Matieres': str(t_matieres),
                    'Niveaux_Autorises': str(t_niveaux),
                    'Heures_Max_Par_Semaine': t_max_h,
                    'Heures_Max_Consecutives': t_max_consec,
                    'Creneaux_Indisponibles': str(t_indispo),
                    'Indice_Flexibilite': t_flex,
                })
                st.success(f"Enseignant '{t_name}' ajoute !")

    _show_editable_table('form_teachers', ['Nom_Enseignant', 'Matieres', 'Heures_Max_Par_Semaine'], 'enseignant')


def _form_rooms(type_etab: str):
    st.markdown("""
    <div class="form-section-title">
        <span class="material-symbols-outlined">meeting_room</span>
        Ajouter une salle
    </div>
    """, unsafe_allow_html=True)
    with st.form("add_room_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<p class="label-caps">TYPE DE SALLE</p>', unsafe_allow_html=True)
            r_type = st.selectbox("Type", TYPES_SALLE, format_func=lambda x: x.replace('_', ' '), label_visibility="collapsed")
        with c2:
            st.markdown('<p class="label-caps">CAPACITE (PLACES)</p>', unsafe_allow_html=True)
            r_cap = st.number_input("Capacite", min_value=5, max_value=500, value=30, label_visibility="collapsed")
        submitted = st.form_submit_button("Ajouter la salle", use_container_width=True)
        if submitted:
            idx = len(st.session_state['form_rooms']) + 1
            st.session_state['form_rooms'].append({
                'ID_Salle': f'SAL_{idx:03d}',
                'Type_Etablissement': type_etab,
                'Capacite': r_cap,
                'Type_Salle': r_type,
            })
            st.success(f"Salle {r_type} ({r_cap} places) ajoutee !")

    _show_editable_table('form_rooms', ['ID_Salle', 'Type_Salle', 'Capacite'], 'salle')


def _form_subjects(type_etab: str):
    st.markdown("""
    <div class="form-section-title">
        <span class="material-symbols-outlined">menu_book</span>
        Ajouter une matiere
    </div>
    """, unsafe_allow_html=True)
    with st.form("add_subject_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<p class="label-caps">NOM DE LA MATIERE</p>', unsafe_allow_html=True)
            m_name = st.selectbox("Matiere", MATIERES_DISPONIBLES, label_visibility="collapsed")
        with c2:
            st.markdown('<p class="label-caps">HEURES / SEMAINE</p>', unsafe_allow_html=True)
            m_hours = st.number_input("Heures", min_value=2, max_value=10, value=4, step=2, label_visibility="collapsed")
        with c3:
            st.markdown('<p class="label-caps">LABORATOIRE</p>', unsafe_allow_html=True)
            m_labo = st.checkbox("Necessite un laboratoire")
        submitted = st.form_submit_button("Ajouter la matiere", use_container_width=True)
        if submitted:
            idx = len(st.session_state['form_subjects']) + 1
            st.session_state['form_subjects'].append({
                'ID_Matiere': f'MAT_{idx:03d}',
                'Nom_Matiere': m_name,
                'Type_Etablissement': type_etab,
                'Heures_Hebdo_Requises': m_hours,
                'Necessite_Labo': m_labo,
            })
            st.success(f"Matiere '{m_name}' ajoutee !")

    _show_editable_table('form_subjects', ['Nom_Matiere', 'Heures_Hebdo_Requises', 'Necessite_Labo'], 'matiere')


def _form_classes(type_etab: str):
    st.markdown("""
    <div class="form-section-title">
        <span class="material-symbols-outlined">school</span>
        Ajouter une classe (groupe)
    </div>
    """, unsafe_allow_html=True)
    with st.form("add_class_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<p class="label-caps">NIVEAU</p>', unsafe_allow_html=True)
            cl_niveau = st.selectbox("Niveau", NIVEAUX_DISPONIBLES, label_visibility="collapsed")
        with c2:
            st.markdown('<p class="label-caps">NOMBRE D\'ETUDIANTS</p>', unsafe_allow_html=True)
            cl_nb = st.number_input("Etudiants", min_value=5, max_value=200, value=30, label_visibility="collapsed")
        submitted = st.form_submit_button("Ajouter la classe", use_container_width=True)
        if submitted:
            idx = len(st.session_state['form_classes']) + 1
            st.session_state['form_classes'].append({
                'ID_Classe': f'CLS_{idx:03d}',
                'Type_Etablissement': type_etab,
                'Niveau': cl_niveau,
                'Nombre_Etudiants': cl_nb,
            })
            st.success(f"Classe {cl_niveau} ({cl_nb} etudiants) ajoutee !")

    # Show group count summary
    classes = st.session_state.get('form_classes', [])
    if classes:
        from collections import Counter
        niveau_counts = Counter(c['Niveau'] for c in classes)
        total_groups = len(classes)
        st.markdown(f"""
        <div class="glass-panel" style="padding:1rem;">
            <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.75rem;">
                <span class="material-symbols-outlined" style="color:var(--secondary);">groups</span>
                <span style="font-weight:700; color:var(--on-surface);">
                    {total_groups} groupe(s) au total
                </span>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:0.5rem;">
                {''.join(f'<span style="background:var(--surface-container-low); border:1px solid var(--outline-variant); border-radius:9999px; padding:4px 12px; font-size:0.75rem; color:var(--on-surface-variant);">{niv.replace("_"," ")} <strong style="color:var(--secondary);">&times;{cnt}</strong></span>' for niv, cnt in sorted(niveau_counts.items()))}
            </div>
        </div>
        """, unsafe_allow_html=True)

    _show_editable_table('form_classes', ['ID_Classe', 'Niveau', 'Nombre_Etudiants'], 'classe')


def _show_editable_table(session_key: str, columns: list, entity_name: str):
    """Display a table with delete buttons for each row."""
    items = st.session_state.get(session_key, [])
    if not items:
        return

    st.markdown(f"**{len(items)} {entity_name}(s) ajoute(s)**")

    # Show table with delete buttons
    for i, item in enumerate(items):
        cols = st.columns([*[3] * len(columns), 1])
        for j, col_name in enumerate(columns):
            val = item.get(col_name, '')
            with cols[j]:
                st.markdown(f'<span style="font-size:0.85rem; color:var(--on-surface);">{val}</span>', unsafe_allow_html=True)
        with cols[-1]:
            if st.button("🗑️", key=f"del_{session_key}_{i}", help=f"Supprimer ce(tte) {entity_name}"):
                st.session_state[session_key].pop(i)
                st.rerun()


# ── Shared Helpers ───────────────────────────────────────────────────────────
REQUIRED_COLUMNS = {
    'enseignants': ['ID_Enseignant', 'Nom_Enseignant', 'Type_Etablissement', 'Matieres',
                    'Niveaux_Autorises', 'Heures_Max_Par_Semaine', 'Heures_Max_Consecutives',
                    'Creneaux_Indisponibles', 'Indice_Flexibilite'],
    'salles': ['ID_Salle', 'Type_Etablissement', 'Capacite', 'Type_Salle'],
    'matieres': ['ID_Matiere', 'Nom_Matiere', 'Type_Etablissement', 'Heures_Hebdo_Requises', 'Necessite_Labo'],
    'classes': ['ID_Classe', 'Type_Etablissement', 'Niveau', 'Nombre_Etudiants'],
}


def _validate_all(df_ens, df_sal, df_mat, df_cls) -> list:
    errors = []
    for name, df in [('enseignants', df_ens), ('salles', df_sal), ('matieres', df_mat), ('classes', df_cls)]:
        missing = [c for c in REQUIRED_COLUMNS[name] if c not in df.columns]
        if missing:
            errors.append(f"**{name}**: Colonnes manquantes: {', '.join(missing)}")
        if len(df) == 0:
            errors.append(f"**{name}**: Le fichier est vide")
    if errors:
        return errors

    types_ens = set(df_ens['Type_Etablissement'].unique())
    types_cls = set(df_cls['Type_Etablissement'].unique())
    types_sal = set(df_sal['Type_Etablissement'].unique())
    types_mat = set(df_mat['Type_Etablissement'].unique())

    if len(types_cls) > 1:
        errors.append(
            f"**classes**: Plusieurs types d'etablissement detectes ({', '.join(sorted(types_cls))}). "
            "Chaque emploi du temps doit concerner un seul type.")

    for t in types_cls:
        if t not in types_ens:
            errors.append(f"**enseignants**: Aucun enseignant pour le type '{t}'")
        if t not in types_sal:
            errors.append(f"**salles**: Aucune salle pour le type '{t}'")
        if t not in types_mat:
            errors.append(f"**matieres**: Aucune matiere pour le type '{t}'")

    labo_types = {'Labo_Science', 'Labo_Informatique', 'Laboratoire'}
    for t in types_mat:
        mats_labo = df_mat[(df_mat['Type_Etablissement'] == t) & (df_mat['Necessite_Labo'] == True)]
        if len(mats_labo) > 0:
            sals_labo = df_sal[(df_sal['Type_Etablissement'] == t) & (df_sal['Type_Salle'].isin(labo_types))]
            if len(sals_labo) == 0:
                noms = ', '.join(mats_labo['Nom_Matiere'].tolist())
                errors.append(
                    f"**salles**: Les matieres [{noms}] ({t}) necessitent un laboratoire, "
                    "mais aucune salle de type labo n'est disponible.")

    return errors


def _store_data(df_ens, df_sal, df_mat, df_cls):
    st.session_state['df_enseignants'] = df_ens
    st.session_state['df_salles'] = df_sal
    st.session_state['df_matieres'] = df_mat
    st.session_state['df_classes'] = df_cls
    st.session_state['data_loaded'] = True


def _show_data_stats(df_ens, df_sal, df_mat, df_cls):
    # Calculate group count by level
    n_groups = len(df_cls)
    level_counts = df_cls['Niveau'].value_counts().to_dict() if 'Niveau' in df_cls.columns else {}
    level_chips = ' '.join(
        f'<span style="background:var(--surface-container-highest); border-radius:9999px; padding:2px 8px; font-size:0.65rem; color:var(--on-surface-variant); margin-right:2px;">{niv.replace("_"," ")} <b style="color:var(--secondary);">&times;{cnt}</b></span>'
        for niv, cnt in sorted(level_counts.items())
    )

    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-card-icon teachers">
                <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">group</span>
            </div>
            <div>
                <div class="stat-card-label">Enseignants</div>
                <div class="stat-card-value">{len(df_ens)}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-card-icon students">
                <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">school</span>
            </div>
            <div>
                <div class="stat-card-label">Classes / Groupes</div>
                <div class="stat-card-value">{n_groups}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-card-icon rooms">
                <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">meeting_room</span>
            </div>
            <div>
                <div class="stat-card-label">Salles</div>
                <div class="stat-card-value">{len(df_sal)}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-card-icon conflicts">
                <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">menu_book</span>
            </div>
            <div>
                <div class="stat-card-label">Matieres</div>
                <div class="stat-card-value">{len(df_mat)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if level_chips:
        st.markdown(f'<div style="margin-top:-1rem; margin-bottom:1rem; display:flex; flex-wrap:wrap; gap:4px;">{level_chips}</div>', unsafe_allow_html=True)


def _show_cta_section():
    st.markdown("""
    <div class="cta-section">
        <h3>Pret a optimiser ?</h3>
        <p>Une fois toutes les entites verifiees, notre moteur IA peut commencer a calculer des millions de permutations pour trouver l'emploi du temps parfait.</p>
    </div>
    """, unsafe_allow_html=True)


# ── Generation Page ──────────────────────────────────────────────────────────
def render_generation_page():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-status">
            <span class="material-symbols-outlined" style="font-size:1rem; vertical-align:middle;">auto_awesome</span>
            Statut du moteur : En attente
        </div>
        <h2>Configuration du Moteur</h2>
        <p>Configurez les parametres heuristiques du moteur OptiPlus. Un nombre de variantes plus eleve offre plus de choix mais augmente le temps de generation.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get('data_loaded'):
        st.warning("Veuillez d'abord charger les donnees dans l'onglet 'Donnees'.")
        return

    col_config, col_status = st.columns([2, 1])

    with col_config:
        st.markdown('<div class="config-panel">', unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:0.5rem;">
            <div>
                <div class="config-title">Nombre de Variantes</div>
                <div class="config-desc">Le nombre total de candidats uniques generes.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        n_variantes = st.slider("Variantes", min_value=3, max_value=20, value=10, label_visibility="collapsed")

        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:0.5rem; margin-top:1.5rem;">
            <div>
                <div class="config-title">Tentatives Maximum</div>
                <div class="config-desc">Tentatives de resolution de conflits par creneau.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        max_retries = st.slider("Retries", min_value=100, max_value=500, value=300, label_visibility="collapsed")

        st.markdown("""
        <div style="margin-top:1.5rem;">
            <div class="config-title">Methode de Scoring</div>
        </div>
        """, unsafe_allow_html=True)
        scoring = st.radio("Scoring", ["Heuristique", "ML (XGBoost)"], horizontal=True, label_visibility="collapsed")
        scoring_method = 'heuristic' if scoring == "Heuristique" else 'ml'

        type_etab = None
        types_in_data = set(st.session_state['df_classes']['Type_Etablissement'].unique())
        if len(types_in_data) == 1:
            type_etab = list(types_in_data)[0]

        with st.expander("Horaires de l'etablissement", expanded=False):
            all_slots = list(ALL_HEURES)
            if type_etab:
                default_slots = HEURES_PAR_TYPE.get(type_etab, all_slots)
                selected_slots = st.multiselect(
                    f"Creneaux horaires ({type_etab.replace('_', ' ')})",
                    all_slots,
                    default=default_slots,
                )
                if selected_slots:
                    custom_heures = {type_etab: selected_slots}
                else:
                    st.warning("Selectionnez au moins un creneau.")
                    custom_heures = None
            else:
                st.info("Les horaires par defaut sont utilises pour chaque type d'etablissement.")
                custom_heures = None

        st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)

        if st.button("Optimiser l'Emploi du Temps", type="primary", use_container_width=True):
            progress = st.progress(0, text="Initialisation du moteur heuristique...")
            t0 = time.time()

            def update(pct):
                msgs = [
                    "Initialisation du moteur heuristique...",
                    "Allocation des salles...",
                    "Detection des collisions...",
                    "Scoring des candidats...",
                    "Optimisation des contraintes...",
                    "Finalisation des resultats...",
                ]
                idx = min(int(pct * len(msgs)), len(msgs) - 1)
                progress.progress(pct, text=msgs[idx])

            variants = generer_n_variantes(
                st.session_state['df_enseignants'],
                st.session_state['df_salles'],
                st.session_state['df_matieres'],
                st.session_state['df_classes'],
                n_variantes=n_variantes,
                max_retries=max_retries,
                progress_callback=update,
                heures_par_type=custom_heures,
            )

            if scoring_method == 'ml':
                progress.progress(1.0, text="Scoring ML en cours...")
                scorer = TimetableScorer()
                variants = scorer.rank_variants(variants, method='ml')

            elapsed = time.time() - t0
            progress.progress(1.0, text="Optimisation terminee !")

            st.session_state['variants'] = variants
            st.session_state['generation_time'] = elapsed

            scores = [v[1] for v in variants]
            st.success(
                f"**{len(variants)}** variantes generees en **{elapsed:.1f}s** — "
                f"Scores: **{min(scores):.1f}** a **{max(scores):.1f}** / 100"
            )

        st.markdown('</div>', unsafe_allow_html=True)

    with col_status:
        st.markdown('<div class="live-progress-panel">', unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div class="config-title">Progression</div>
        </div>
        """, unsafe_allow_html=True)

        if 'variants' in st.session_state:
            elapsed = st.session_state.get('generation_time', 0)
            n_vars = len(st.session_state['variants'])
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:1rem;">
                <span style="width:8px; height:8px; border-radius:50%; background:#2ECC71;"></span>
                <span style="font-size:0.85rem; color:var(--on-surface-variant);">Optimisation reussie. Resultats prets.</span>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:var(--secondary); margin-bottom:0.5rem;">
                {n_vars} variantes en {elapsed:.1f}s
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <span style="width:8px; height:8px; border-radius:50%; background:var(--primary); animation:pulse 2s infinite;"></span>
                <span style="font-size:0.85rem; color:var(--on-surface-variant);">En attente d'instructions...</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="live-progress-panel" style="margin-top:1rem;">', unsafe_allow_html=True)
        st.markdown('<div class="config-title" style="margin-bottom:1rem;">Resume des Donnees</div>', unsafe_allow_html=True)
        if st.session_state.get('data_loaded'):
            n_ens = len(st.session_state['df_enseignants'])
            n_cls = len(st.session_state['df_classes'])
            n_sal = len(st.session_state['df_salles'])
            st.markdown(f"""
            <div class="input-summary-item">
                <div class="input-summary-icon" style="color:var(--primary);">
                    <span class="material-symbols-outlined">group</span>
                </div>
                <div>
                    <div class="input-summary-label">Enseignants</div>
                    <div class="input-summary-value">{n_ens}</div>
                </div>
            </div>
            <div class="input-summary-item">
                <div class="input-summary-icon" style="color:var(--secondary);">
                    <span class="material-symbols-outlined">school</span>
                </div>
                <div>
                    <div class="input-summary-label">Classes</div>
                    <div class="input-summary-value">{n_cls}</div>
                </div>
            </div>
            <div class="input-summary-item">
                <div class="input-summary-icon" style="color:var(--tertiary);">
                    <span class="material-symbols-outlined">meeting_room</span>
                </div>
                <div>
                    <div class="input-summary-label">Salles</div>
                    <div class="input-summary-value">{n_sal}</div>
                </div>
            </div>
            <div class="ready-badge">
                <span class="material-symbols-outlined ready-badge-icon">check_circle</span>
                <div>
                    <div class="ready-badge-title">Pret pour la generation</div>
                    <div class="ready-badge-desc">Toutes les contraintes verifiees.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if len(types_in_data) > 1:
        st.warning(
            f"Attention : vos donnees contiennent plusieurs types d'etablissement "
            f"({', '.join(sorted(types_in_data))}). L'emploi du temps sera genere "
            f"separement par type."
        )


# ── Results Page ─────────────────────────────────────────────────────────────
def render_results_page():
    if 'variants' not in st.session_state or not st.session_state['variants']:
        st.markdown("""
        <div class="page-header">
            <h2>Resultats de l'Optimisation</h2>
            <p>Lancez d'abord la generation dans l'onglet 'Generation'.</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("Aucun resultat disponible. Lancez d'abord la generation.")
        return

    variants = st.session_state['variants']
    top3 = variants[:3]
    elapsed = st.session_state.get('generation_time', 0)

    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-status">
            <span class="material-symbols-outlined" style="font-size:1rem; vertical-align:middle;">assessment</span>
            Run ID: #OPT-{int(time.time()) % 10000:04d}
        </div>
        <h2>Resultats de l'Optimisation</h2>
        <p>{len(variants)} variantes analysees. Top 3 solutions viables identifiees.</p>
    </div>
    """, unsafe_allow_html=True)

    badge_labels = ["#1 MEILLEUR", "#2 EQUILIBRE", "#3 ALTERNATIF"]
    badge_classes = ["result-badge-1", "result-badge-2", "result-badge-3"]
    card_classes = ["result-card-1", "result-card-2", "result-card-3"]
    score_classes = ["result-score-1", "", ""]

    col1, col2, col3 = st.columns(3)

    for idx, (col, (df_emp, score, details)) in enumerate(zip([col1, col2, col3], top3)):
        with col:
            pen_profs = details.get('penalite_trous_profs', 0)
            pen_classes = details.get('penalite_trous_classes', 0)
            pen_salles = details.get('penalite_salles', 0)
            pen_surcharge = details.get('penalite_surcharge', 0)
            total = details.get('total_seances', 0)

            st.markdown(f"""
            <div class="result-card {card_classes[idx]}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem;">
                    <span class="result-badge {badge_classes[idx]}">{badge_labels[idx]}</span>
                    <div class="result-score {score_classes[idx]}">
                        <span class="result-score-value">{score:.1f}</span>
                        <span class="result-score-max">/100</span>
                    </div>
                </div>
                <div style="margin-top:1rem;">
                    <div class="result-detail-row">
                        <span class="result-detail-label">Trous Enseignants</span>
                        <span class="result-detail-value">{pen_profs:.0f}</span>
                    </div>
                    <div class="result-detail-row">
                        <span class="result-detail-label">Trous Classes</span>
                        <span class="result-detail-value">{pen_classes:.0f}</span>
                    </div>
                    <div class="result-detail-row">
                        <span class="result-detail-label">Salles Sous-utilisees</span>
                        <span class="result-detail-value">{pen_salles:.0f}</span>
                    </div>
                    <div class="result-detail-row">
                        <span class="result-detail-label">Surcharge Journaliere</span>
                        <span class="result-detail-value">{pen_surcharge:.0f}</span>
                    </div>
                    <div class="result-detail-row" style="border:none;">
                        <span class="result-detail-label">Total Seances</span>
                        <span class="result-detail-value" style="color:var(--secondary);">{total}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Apercu de l'emploi du temps"):
                fc1, fc2, fc3 = st.columns(3)
                classes_list = sorted(df_emp['ID_Classe'].unique())
                jours_list = sorted(df_emp['Jour'].unique())
                profs_list = sorted(df_emp['Nom_Enseignant'].unique()) if 'Nom_Enseignant' in df_emp.columns else []
                with fc1:
                    sel_cls = st.selectbox("Classe", ["Toutes"] + list(classes_list), key=f"rcls_{idx}")
                with fc2:
                    sel_jour = st.selectbox("Jour", ["Tous"] + list(jours_list), key=f"rjour_{idx}")
                with fc3:
                    sel_prof = st.selectbox("Enseignant", ["Tous"] + list(profs_list), key=f"rprof_{idx}")

                df_disp = df_emp.copy()
                if sel_cls != "Toutes":
                    df_disp = df_disp[df_disp['ID_Classe'] == sel_cls]
                if sel_jour != "Tous":
                    df_disp = df_disp[df_disp['Jour'] == sel_jour]
                if sel_prof != "Tous":
                    df_disp = df_disp[df_disp['Nom_Enseignant'] == sel_prof]

                view_mode = st.radio("Affichage", ["Grille visuelle", "Tableau de donnees"], horizontal=True, key=f"vmode_{idx}", label_visibility="collapsed")

                if view_mode == "Grille visuelle" and sel_cls != "Toutes":
                    _render_timetable_grid(df_disp, sel_cls)
                elif view_mode == "Grille visuelle" and sel_cls == "Toutes" and len(classes_list) <= 5:
                    for cl in classes_list:
                        st.markdown(f'<p class="label-caps" style="margin-top:1rem;">{cl}</p>', unsafe_allow_html=True)
                        _render_timetable_grid(df_disp[df_disp['ID_Classe'] == cl], cl)
                else:
                    st.dataframe(
                        df_disp[['ID_Classe', 'Nom_Matiere', 'Nom_Enseignant', 'ID_Salle', 'Jour', 'Heure_Debut', 'Heure_Fin']]
                        .sort_values(['Jour', 'Heure_Debut']),
                        use_container_width=True, height=300,
                    )

            csv_data = df_emp.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"Telecharger CSV ({badge_labels[idx]})",
                data=csv_data,
                file_name=f"emploi_du_temps_{idx + 1}.csv",
                mime='text/csv',
                use_container_width=True,
            )

    st.markdown('<div style="margin:2rem 0;"></div>', unsafe_allow_html=True)

    with st.expander("Classement complet de toutes les variantes"):
        rows = []
        for i, (_, sc, det) in enumerate(variants):
            rows.append({
                'Rang': i + 1,
                'Score': round(sc, 2),
                'Seances': det.get('total_seances', 0),
                'Pen. Profs': round(det.get('penalite_trous_profs', 0), 1),
                'Pen. Classes': round(det.get('penalite_trous_classes', 0), 1),
                'Pen. Salles': round(det.get('penalite_salles', 0), 1),
                'Pen. Surcharge': round(det.get('penalite_surcharge', 0), 1),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ── Timetable Visual Grid ────────────────────────────────────────────────────
SUBJECT_COLORS = {}
_COLOR_CYCLE = ['v1', 'v2', 'v3', 'v4', 'v5', 'v6']


def _subj_color(subj: str) -> str:
    if subj not in SUBJECT_COLORS:
        SUBJECT_COLORS[subj] = _COLOR_CYCLE[len(SUBJECT_COLORS) % len(_COLOR_CYCLE)]
    return SUBJECT_COLORS[subj]


def _render_timetable_grid(df: pd.DataFrame, class_id: str):
    """Render a visual timetable grid for a single class."""
    if df.empty:
        st.info("Aucune seance pour cette selection.")
        return

    jours_present = sorted(df['Jour'].unique())
    if not jours_present:
        return

    # Determine time slots from data
    time_slots = []
    for _, row in df.iterrows():
        slot = f"{row['Heure_Debut']}-{row['Heure_Fin']}"
        if slot not in time_slots:
            time_slots.append(slot)
    # Sort by start hour
    time_slots.sort(key=lambda s: int(s.split(':')[0]))

    # Build lookup
    lookup = {}
    for _, row in df.iterrows():
        key = (row['Jour'], f"{row['Heure_Debut']}-{row['Heure_Fin']}")
        lookup[key] = row

    # Build HTML table
    html = '<table class="tt-visual"><thead><tr><th></th>'
    for j in jours_present:
        html += f'<th>{j}</th>'
    html += '</tr></thead><tbody>'

    for slot in time_slots:
        html += f'<tr><th style="white-space:nowrap;">{slot}</th>'
        for jour in jours_present:
            row = lookup.get((jour, slot))
            if row is not None:
                subj = row.get('Nom_Matiere', '?')
                prof = row.get('Nom_Enseignant', '')
                salle = row.get('ID_Salle', '')
                color = _subj_color(subj)
                html += f'''<td>
                    <div class="tt-cell tt-cell-filled tt-cell-{color}">
                        <div class="tt-subj">{subj}</div>
                        <div class="tt-prof">{prof}</div>
                        <div class="tt-room">{salle}</div>
                    </div>
                </td>'''
            else:
                html += '<td><div class="tt-cell tt-cell-empty">—</div></td>'
        html += '</tr>'

    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    inject_css()

    if not st.session_state.get('authenticated'):
        render_auth_page()
        return

    render_navbar()

    tab_data, tab_gen, tab_results = st.tabs([
        "Donnees",
        "Generation",
        "Resultats",
    ])

    with tab_data:
        render_data_page()
    with tab_gen:
        render_generation_page()
    with tab_results:
        render_results_page()


if __name__ == '__main__':
    main()
