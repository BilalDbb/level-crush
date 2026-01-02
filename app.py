import streamlit as st
import json
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONNEXION SUPABASE ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur Cloud : {e}")
    st.stop()

# --- 2. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data and len(response.data) > 0:
            raw_data = response.data[0]['data']
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            if "stats" not in data: 
                data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            if "completed_quests" not in data: 
                data["completed_quests"] = []
            return data
    except: pass
    return {"level": 1, "xp": 0, "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}, "completed_quests": []}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

# --- 3. CALCULS ---
def get_xp_needed(lvl):
    exponent = 1.25 
    coeff = 200 if lvl < 5 else 25
    xp_palier = int(coeff * (lvl**exponent))
    return xp_palier * 2 if lvl == 100 else xp_palier

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="centered")
st.title("⚡ LEVEL CRUSH")

xp_target = get_xp_needed(user['level'])
col_lvl, col_xp = st.columns(2)
col_lvl.metric("NIVEAU", user['level'])
col_xp.metric("XP", f"{user['xp']} / {xp_target}")
st.progress(min(user['xp'] / xp_target, 1.0))

tab_quests, tab_stats = st.tabs(["⚔️ Quêtes", "📊 État de Puissance"])

with tab_quests:
    # Définition des catégories de quêtes avec tes paliers de poids
    quest_types = {
        "Quotidiennes": {"base": 150, "max_w": 3, "tasks": ["Pompes", "Abdos", "Lecture", "Rangement"]},
        "Hebdomadaires": {"base": 500, "max_w": 5, "tasks": ["Grand Ménage", "Bilan Hebdo"]},
        "Mensuelles": {"base": 1500, "max_w": 7, "tasks": ["Objectif Majeur"]},
        "Trimestrielles": {"base": 3000, "max_w": 9, "tasks": ["Changement de Vie"]},
        "Annuelles": {"base": 10000, "max_w": 11, "tasks": ["Accomplissement Légendaire"]}
    }

    for q_type, q_info in quest_types.items():
        with st.expander(f"{q_type} (Poids 1-{q_info['max_w']})", expanded=(q_type == "Quotidiennes")):
            for t_name in q_info["tasks"]:
                t_id = f"{q_type}_{t_name}"
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                is_done = t_id in user["completed_quests"]
                
                c1.write(f"{'✅' if is_done else '🔳'} **{t_name}**")
                
                if not is_done:
                    chosen_stat = c2.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"], key=f"s_{t_id}")
                    weight = c3.select_slider("Poids", options=list(range(1, q_info['max_w'] + 1)), key=f"w_{t_id}")
                    
                    if c4.button("Valider", key=t_id, use_container_width=True):
                        user['xp'] += (q_info['base'] * weight)
                        user['stats'][chosen_stat] += weight
                        user["completed_quests"].append(t_id)
                        while user['xp'] >= get_xp_needed(user['level']):
                            user['xp'] -= get_xp_needed(user['level'])
                            user['level'] += 1
                        save_data(user)
                        st.rerun()
                else:
                    c4.button("Fait", key=t_id, disabled=True, use_container_width=True)

with tab_stats:
    st.subheader("📊 Caractéristiques")
    s_col1, s_col2 = st.columns(2)
    s_col1.metric("💪 Physique", user['stats']['Physique'])
    s_col1.metric("🧠 Connaissances", user['stats']['Connaissances'])
    s_col2.metric("🛠️ Autonomie", user['stats']['Autonomie'])
    s_col2.metric("🧘 Mental", user['stats']['Mental'])

with st.sidebar:
    st.header("⚙️ Système")
    if st.button("🔄 Nouvelle Journée (Quotidiennes uniquement)"):
        # On ne reset que les quêtes qui commencent par "Quotidiennes"
        user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith("Quotidiennes")]
        save_data(user)
        st.rerun()
    if st.button("⚠️ Reset Hebdo"):
        user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith("Hebdomadaires")]
        save_data(user)
        st.rerun()
    st.divider()
    st.json(user)
