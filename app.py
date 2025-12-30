import streamlit as st
import json
import random
from supabase import create_client, Client

# --- 1. CONNEXION SUPABASE ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Erreur de configuration des Secrets.")
    st.stop()

# --- 2. CONFIGURATION DU JEU ---
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    st.error("Fichier config.json introuvable.")
    st.stop()

# --- 3. FONCTIONS DE SAUVEGARDE ---
MY_ID = "chasseur_unique_01" 

def load_from_supabase():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['data']
    except Exception as e:
        st.warning(f"Note : Lecture impossible ({e}).")
    return {"level": 1, "xp": 0}

def save_to_supabase(data):
    try:
        # On utilise .execute() et on attend la réponse pour être sûr que c'est écrit
        supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

# Initialisation de la donnée (si elle n'existe pas déjà dans cette session)
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_from_supabase()

# On crée un raccourci pour manipuler les données plus facilement
user = st.session_state.user_data

# --- 4. LOGIQUE XP ---
def get_xp_needed(lvl):
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    xp = int(coeff * (lvl**config['settings']['exponent']))
    if lvl == 100: xp = xp * 2
    return xp

# --- 5. INTERFACE (UI) ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")

quotes = [
    "« Le seul moyen de devenir plus fort est de se battre contre soi-même. » — Solo Leveling",
    "« Si tu n'aimes pas ton destin, ne l'accepte pas. » — Naruto",
    "« Les limites n'existent que si tu les laisses exister. » — Vegeta (DBZ)",
    "« Travailler dur est inutile pour ceux qui ne croient pas en eux-mêmes. » — Naruto"
]

st.info(random.choice(quotes))
st.title(f"⚡ {config['settings']['app_name']}")

xp_target = get_xp_needed(user['level'])

col1, col2 = st.columns(2)
with col1:
    st.metric("Niveau actuel", user['level'])
with col2:
    st.metric("XP Totale", user['xp'])

progress = min(user['xp'] / xp_target, 1.0)
st.progress(progress)
st.caption(f"XP : {user['xp']} / {xp_target}")

st.divider()

st.subheader("⚔️ Quête en cours")
if st.button(f"S'entraîner dur (+215 XP)"):
    # Mise à jour des valeurs
    user['xp'] += 215
    if user['xp'] >= xp_target:
        user['level'] += 1
        user['xp'] = 0
        st.balloons()
        st.success(f"NIVEAU SUPÉRIEUR : {user['level']} !")
    
    # SAUVEGARDE
    save_to_supabase(user)
    
    # On force la session Streamlit à enregistrer les changements avant de recharger
    st.session_state.user_data = user
    st.rerun()

with st.expander("🔍 Logs du Système"):
    st.json(st.session_state.user_data)
