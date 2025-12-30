import streamlit as st
import json
from supabase import create_client, Client

# --- CONNEXION SUPABASE ---
# On va chercher les clés dans les Secrets de Streamlit pour la sécurité
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- CONFIGURATION DU JEU ---
with open('config.json', 'r') as f:
    config = json.load(f)

# --- FONCTIONS DE SAUVEGARDE AUTOMATIQUE ---
def load_from_supabase(user_id="mon_user_unique"):
    # On cherche dans la table 'profiles' l'entrée qui correspond à ton ID
    response = supabase.table('profiles').select('data').eq('user_id', user_id).execute()
    if len(response.data) > 0:
        return response.data[0]['data']
    return {"level": 1, "xp": 0}

def save_to_supabase(data, user_id="mon_user_unique"):
    # On met à jour la base de données instantanément
    supabase.table('profiles').upsert({"user_id": user_id, "data": data}).execute()

# Initialisation
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_from_supabase()

user = st.session_state.user_data

# --- LOGIQUE XP (Inchangée) ---
def get_xp_needed(lvl):
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    xp = int(coeff * (lvl**config['settings']['exponent']))
    if lvl == 100: xp = xp * 2
    return xp

# --- INTERFACE ---
st.title("⚡ LEVEL CRUSH : AUTO-SAVE")

xp_target = get_xp_needed(user['level'])

if st.button("Terminer Quête (+215 XP)"):
    user['xp'] += 215
    if user['xp'] >= xp_target:
        user['level'] += 1
        user['xp'] = 0
        st.balloons()
    
    # SAUVEGARDE AUTOMATIQUE
    save_to_supabase(user)
    st.success("Progression synchronisée avec le Cloud !")
    st.rerun()

st.metric("Niveau actuel", user['level'])
st.progress(min(user['xp'] / xp_target, 1.0))
st.write(f"XP : {user['xp']} / {xp_target}")
