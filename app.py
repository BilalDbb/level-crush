import streamlit as st
import json
from supabase import create_client, Client

# --- 1. CONNEXION SUPABASE ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Clés de configuration manquantes dans les Secrets Streamlit.")
    st.stop()

# --- 2. CONFIGURATION DU JEU ---
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    st.error("Fichier config.json introuvable.")
    st.stop()

# --- 3. FONCTIONS DE SAUVEGARDE ---
# ID unique pour identifier ton profil dans la table
MY_ID = "chasseur_unique_01" 

def load_from_supabase():
    try:
        # On cherche la ligne où user_id correspond à notre ID
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['data']
    except Exception as e:
        st.warning(f"Note : Lecture impossible ({e}). Profil local actif.")
    return {"level": 1, "xp": 0}

def save_to_supabase(data):
    try:
        # On enregistre la donnée. user_id doit être de type TEXT dans Supabase.
        supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

# Initialisation
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_from_supabase()

user = st.session_state.user_data

# --- 4. LOGIQUE XP ---
def get_xp_needed(lvl):
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    xp = int(coeff * (lvl**config['settings']['exponent']))
    if lvl == 100: xp = xp * 2
    return xp

# --- 5. INTERFACE (UI) ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")
st.title(f"⚡ {config['settings']['app_name']}")

xp_target = get_xp_needed(user['level'])

col1, col2 = st.columns(2)
with col1:
    st.metric("Niveau actuel", user['level'])
with col2:
    st.metric("XP Totale", user['xp'])

progress = min(user['xp'] / xp_target, 1.0)
st.progress(progress)

st.divider()

st.subheader("⚔️ Entraînement")
if st.button(f"Terminer une Quête (+215 XP)"):
    user['xp'] += 215
    if user['xp'] >= xp_target:
        user['level'] += 1
        user['xp'] = 0
        st.balloons()
    
    save_to_supabase(user)
    st.rerun()

with st.expander("🔍 Debugging Data"):
    st.json(user)
