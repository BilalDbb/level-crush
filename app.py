import streamlit as st
import json
import random
from supabase import create_client, Client

# --- 1. CONNEXION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur de connexion Cloud : {e}")
    st.stop()

with open('config.json', 'r') as f:
    config = json.load(f)

# --- 2. LOGIQUE DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    """Récupère et nettoie la donnée de Supabase."""
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data and len(response.data) > 0:
            raw_data = response.data[0]['data']
            
            # SECURITÉ : Si Supabase renvoie du texte au lieu d'un dictionnaire, on le convertit
            if isinstance(raw_data, str):
                return json.loads(raw_data)
            return raw_data
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
    
    # Si rien n'est trouvé, profil par défaut
    return {"level": 1, "xp": 0}

def save_data(data):
    """Enregistre la donnée proprement."""
    try:
        supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()
    except Exception as e:
        st.error(f"Erreur d'écriture : {e}")

# --- 3. GESTION DE LA SESSION ---
# On s'assure que session_state est TOUJOURS synchronisé
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

# --- 4. CALCULS ---
def get_xp_needed(lvl):
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    return int(coeff * (lvl**config['settings']['exponent']))

# --- 5. UI ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")

st.title(f"⚡ {config['settings']['app_name']}")

# On travaille directement sur la session_state pour éviter les décalages
user = st.session_state.user_data
xp_target = get_xp_needed(user['level'])

st.metric("NIVEAU ACTUEL", user['level'])
st.progress(min(user['xp'] / xp_target, 1.0))
st.caption(f"XP : {user['xp']} / {xp_target}")

st.divider()

if st.button("🔥 EXÉCUTER QUÊTE (+215 XP)", use_container_width=True):
    # Mise à jour
    st.session_state.user_data['xp'] += 215
    if st.session_state.user_data['xp'] >= xp_target:
        st.session_state.user_data['level'] += 1
        st.session_state.user_data['xp'] = 0
        st.balloons()
    
    # Sauvegarde du nouvel état
    save_data(st.session_state.user_data)
    st.rerun()

# --- 6. DEBUG (Très important ici) ---
with st.sidebar:
    st.header("⚙️ Système")
    if st.button("🔄 Forcer Synchro"):
        st.session_state.user_data = load_data()
        st.rerun()
    
    st.divider()
    st.write("Données brutes détectées :")
    st.json(st.session_state.user_data)
