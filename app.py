import streamlit as st
import json
import random
from supabase import create_client, Client

# --- 1. CONNEXION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Erreur de connexion Cloud.")
    st.stop()

with open('config.json', 'r') as f:
    config = json.load(f)

# --- 2. LOGIQUE DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    try:
        # On demande la donnée et on trie par date de création (au cas où)
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).order('created_at', descending=True).limit(1).execute()
        if response.data:
            return response.data[0]['data']
    except Exception:
        pass
    return {"level": 1, "xp": 0}

def save_data(data):
    # L'upsert va maintenant fonctionner parfaitement car user_id sera l'unique identifiant
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

# --- 3. SESSION ---
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

# --- 4. CALCULS ---
def get_xp_needed(lvl):
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    return int(coeff * (lvl**config['settings']['exponent']))

# --- 5. UI ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")

st.info(random.choice([
    "« Un Chasseur n'attend pas, il provoque sa chance. »",
    "« Ta seule limite est celle que tu t'imposes. »"
]))

st.title(f"⚡ {config['settings']['app_name']}")
xp_target = get_xp_needed(user['level'])

st.metric("NIVEAU", user['level'])
st.progress(min(user['xp'] / xp_target, 1.0))
st.caption(f"XP : {user['xp']} / {xp_target}")

if st.button("🔥 EXÉCUTER QUÊTE (+215 XP)", use_container_width=True):
    user['xp'] += 215
    if user['xp'] >= xp_target:
        user['level'] += 1
        user['xp'] = 0
        st.balloons()
    
    save_data(user)
    st.session_state.user_data = user
    st.rerun()

with st.sidebar:
    if st.button("🔄 Synchro"):
        st.session_state.user_data = load_data()
        st.rerun()
