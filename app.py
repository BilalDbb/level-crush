import streamlit as st
import json
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONNEXION SUPABASE ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur de connexion Cloud : {e}")
    st.stop()

# --- 2. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data and len(response.data) > 0:
            raw_data = response.data[0]['data']
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            
            # Initialisation des listes si elles n'existent pas encore
            if "task_lists" not in data:
                data["task_lists"] = {
                    "Quotidiennes": ["Pompes", "Abdos", "Lecture", "Rangement"],
                    "Hebdomadaires": [],
                    "Mensuelles": [],
                    "Trimestrielles": [],
                    "Annuelles": []
                }
            if "stats" not in data: 
                data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            if "completed_quests" not in data: 
                data["completed_quests"] = []
            return data
    except: pass
    return {
        "level": 1, "xp": 0, 
        "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0},
        "completed_quests": [],
        "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}
    }

def save_data(data):
    try:
        supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

# Initialisation session Streamlit
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

# --- 3. CALCULS ---
def get_xp_needed(lvl):
    exponent = 1.25 #
    coeff = 200 if lvl < 5 else 25 #
    xp_palier = int(coeff * (lvl**exponent))
    return xp_palier * 2 if lvl == 100 else xp_palier

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="centered")

# HUD Supérieur
xp_target = get_xp_needed(user['level'])
st.title(f"⚡ NIVEAU {user['level']}")
st.progress(min(user['xp'] / xp_target, 1.0))
st.caption(f"XP : {user['xp']} / {xp_target}")

# Création des onglets
tab_quests, tab_stats, tab_config = st.tabs(["⚔️ Quêtes", "📊 État", "⚙️ Config"])

# Configuration des récompenses
quest_configs = {
    "Quotidiennes": {"base": 150, "max_w": 3},
    "Hebdomadaires": {"base": 500, "max_w": 5},
    "Mensuelles": {"base": 1500, "max_w": 7},
    "Trimestrielles": {"base": 3000, "max_w": 9},
    "Annuelles": {"base": 10000, "max_w": 11}
}

# --- ONGLET 1 : QUÊTES ---
with tab_quests:
    st.subheader("📋 Objectifs Actuels")
    
    any_task = False
    for q_type, q_info in quest_configs.items():
        tasks = user["task_lists"].get(q_type, [])
        if tasks:
            any_task = True
            with st.expander(f"{q_type} ({len(tasks)})"):
                for t_name in tasks:
                    t_id = f"{q_type}_{t_name}"
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    is_done = t_id in user["completed_quests"]
                    
                    c1.write(f"{'✅' if is_done else '🔳'} {t_name}")
                    
                    if not is_done:
                        s = c2.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"], key=f"s_{t_id}")
                        w = c3.select_slider("Poids", options=list(range(1, q_info['max_w'] + 1)), key=f"w_{t_id}")
                        
                        if c4.button("Valider", key=t_id, use_container_width=True):
                            user['xp'] += (q_info['base'] * w)
                            user['stats'][s] += w
                            user["completed_quests"].append(t_id)
                            # Gestion passage niveau
                            while user['xp'] >= get_xp_needed(user['level']):
                                user['xp'] -= get_xp_needed(user['level'])
                                user['level'] += 1
                            save_data(user)
                            st.rerun()
                    else:
