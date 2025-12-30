import streamlit as st
import json
import random
from supabase import create_client, Client

# --- 1. INITIALISATION DU SYSTÈME ---
# Connexion sécurisée à la base de données via les Secrets
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Échec de connexion au Système. Vérifie tes Secrets Streamlit.")
    st.stop()

# Chargement de la configuration (règles d'XP)
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    st.error("Fichier config.json introuvable sur GitHub.")
    st.stop()

# --- 2. GESTION DES DONNÉES (SUPABASE) ---
MY_ID = "shadow_monarch_01" 

def load_data():
    """Récupère ton profil depuis le Cloud ou crée un profil neuf."""
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            return response.data[0]['data']
    except Exception:
        pass # En cas d'erreur, on renvoie le profil par défaut ci-dessous
    return {"level": 1, "xp": 0}

def save_data(data):
    """Enregistre instantanément ta progression sur le Cloud."""
    # Grâce à ta 'Primary Key' sur user_id, Supabase sait qu'il doit écraser la ligne
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

# --- 3. CHARGEMENT DE LA SESSION ---
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

# --- 4. LOGIQUE DU MOTEUR D'XP ---
def get_xp_needed(lvl):
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    xp = int(coeff * (lvl**config['settings']['exponent']))
    return xp * 2 if lvl == 100 else xp

# --- 5. INTERFACE UTILISATEUR (UI) ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="centered")

# Système d'immersion (Citations)
quotes = [
    "« Le seul moyen de devenir plus fort est de se battre contre soi-même. »",
    "« L'échec est le sel qui donne sa saveur à la victoire. »",
    "« Ne t'arrête pas quand tu es fatigué, arrête-toi quand tu as fini. »"
]
st.info(random.choice(quotes))

# Affichage des statistiques
st.title(f"⚡ {config['settings']['app_name']}")
xp_target = get_xp_needed(user['level'])

col1, col2 = st.columns(2)
col1.metric("NIVEAU", user['level'])
col2.metric("XP", f"{user['xp']} / {xp_target}")

st.progress(min(user['xp'] / xp_target, 1.0))

st.divider()

# Action de Quête
st.subheader("⚔️ ENTRAÎNEMENT")
if st.button("🔥 EXÉCUTER LA QUÊTE (+215 XP)", use_container_width=True):
    user['xp'] += 215
    
    # Montée de niveau
    if user['xp'] >= xp_target:
        user['level'] += 1
        user['xp'] = 0
        st.balloons()
        st.success(f"NIVEAU ATTEINT : {user['level']} !")
    
    # Synchronisation immédiate
    save_data(user)
    st.session_state.user_data = user
    st.rerun()

# --- 6. BARRE LATÉRALE (OPTIONS) ---
with st.sidebar:
    st.header("⚙️ SYSTÈME")
    if st.button("🔄 Forcer la Synchro"):
        st.session_state.user_data = load_data()
        st.rerun()
