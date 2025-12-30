import streamlit as st
import json
import random
from supabase import create_client, Client

# --- 1. CONNEXION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur Cloud : {e}")
    st.stop()

with open('config.json', 'r') as f:
    config = json.load(f)

# --- 2. LOGIQUE DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data and len(response.data) > 0:
            raw_data = response.data[0]['data']
            return json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except: pass
    return {"level": 1, "xp": 0}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

# --- 3. SESSION ---
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

if 'completed_quests' not in st.session_state:
    st.session_state.completed_quests = []

# --- 4. CALCULS (Selon ton tableau de bord) ---
def get_xp_needed(lvl):
    # Utilisation des coefficients précis de ton image
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    xp_palier = int(coeff * (lvl**config['settings']['exponent']))
    return xp_palier * 2 if lvl == 100 else xp_palier

# --- 5. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")

st.title(f"⚡ {config['settings']['app_name']}")

xp_target = get_xp_needed(user['level'])

# Affichage HUD
col1, col2 = st.columns(2)
col1.metric("NIVEAU", user['level'])
col2.metric("XP ACTUELLE", f"{user['xp']} / {xp_target}")

st.progress(min(user['xp'] / xp_target, 1.0))

st.divider()

# --- SYSTÈME DE QUÊTES AVEC PONDÉRATION (1 à 4) ---
st.subheader("📋 Objectifs du Jour")

# Définition des tâches avec leur poids (1 à 4)
# Base XP est de 215 d'après ton tableau
BASE_XP = config['settings']['base_xp'] 

daily_tasks = [
    {"id": "pushups", "name": "💪 Faire 100 pompes", "weight": 3}, # Poids 3 (Intense)
    {"id": "abs", "name": "🧘 Faire 100 abdos", "weight": 2},     # Poids 2 (Moyen)
    {"id": "read", "name": "📖 Lire 20 pages", "weight": 1},      # Poids 1 (Régulier)
]

for task in daily_tasks:
    c1, c2 = st.columns([3, 1])
    
    is_done = task['id'] in st.session_state.completed_quests
    gain_xp = BASE_XP * task['weight']
    
    status_icon = "✅" if is_done else "🔳"
    c1.write(f"{status_icon} **{task['name']}**")
    c1.caption(f"Difficulté : Poids {task['weight']} | Récompense : +{gain_xp} XP")
    
    if not is_done:
        if c2.button("Valider", key=task['id'], use_container_width=True):
            user['xp'] += gain_xp
            st.session_state.completed_quests.append(task['id'])
            
            if user['xp'] >= xp_target:
                user['level'] += 1
                user['xp'] = 0
                st.balloons()
            
            save_data(user)
            st.rerun()
    else:
        c2.button("Terminé", key=task['id'], disabled=True, use_container_width=True)

# --- 6. BARRE LATÉRALE ---
with st.sidebar:
    if st.button("🔄 Nouvelle Journée (Reset)"):
        st.session_state.completed_quests = []
        st.rerun()
    st.divider()
    st.write("Calculateur :")
    st.info(f"Base XP ({BASE_XP}) x Poids = Gain")
