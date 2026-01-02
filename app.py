import streamlit as st
import json
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONNEXION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur Cloud : {e}")
    st.stop()

# --- 2. LOGIQUE DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data and len(response.data) > 0:
            raw_data = response.data[0]['data']
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            # Initialisations de sécurité
            if "stats" not in data:
                data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            if "history" not in data:
                data["history"] = []
            if "completed_today" not in data:
                data["completed_today"] = []
            return data
    except: pass
    return {
        "level": 1, "xp": 0, 
        "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0},
        "completed_today": [],
        "history": []
    }

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

# --- 3. CHARGEMENT ---
user = load_data()

# --- 4. CALCULS ---
def get_xp_needed(lvl):
    exponent = 1.25 
    coeff = 200 if lvl < 5 else 25
    xp_palier = int(coeff * (lvl**exponent))
    return xp_palier * 2 if lvl == 100 else xp_palier

# --- 5. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")
st.title("⚡ LEVEL CRUSH")

xp_target = get_xp_needed(user['level'])

# HUD
col1, col2 = st.columns(2)
col1.metric("NIVEAU GLOBAL", user['level'])
col2.metric("XP", f"{user['xp']} / {xp_target}")
st.progress(min(user['xp'] / xp_target, 1.0))

# STATS (Noms Complets)
st.write("### 📊 Caractéristiques")
s_col1, s_col2, s_col3, s_col4 = st.columns(4)
s_col1.metric("Physique", user['stats']['Physique'])
s_col2.metric("Connaissances", user['stats']['Connaissances'])
s_col3.metric("Autonomie", user['stats']['Autonomie'])
s_col4.metric("Mental", user['stats']['Mental'])

st.divider()

# --- SYSTÈME DE QUÊTES ---
st.subheader("📋 Objectifs du Jour")

BASE_XP = 150 
daily_tasks = [
    {"id": "pushups", "name": "💪 Faire 100 pompes", "stat": "Physique"}, 
    {"id": "abs", "name": "🧘 Faire 100 abdos", "stat": "Physique"},     
    {"id": "read", "name": "📖 Lire 20 pages", "stat": "Connaissances"},
    {"id": "clean", "name": "🛠️ Rangement / Autonomie", "stat": "Autonomie"},
]

for task in daily_tasks:
    c1, c2, c3 = st.columns([2, 1, 1])
    is_done = task['id'] in user["completed_today"]
    
    # Nom de la tâche
    status_icon = "✅" if is_done else "🔳"
    c1.write(f"{status_icon} **{task['name']}**")
    
    if not is_done:
        # Choix de la pondération (Poids)
        weight = c2.select_slider("Poids", options=[1, 2, 3], key=f"w_{task['id']}")
        
        if c3.button("Valider", key=task['id'], use_container_width=True):
            gain_xp = BASE_XP * weight
            # Mise à jour profil
            user['xp'] += gain_xp
            user['stats'][task['stat']] += weight
            user["completed_today"].append(task['id'])
            
            # Enregistrement Journal (Date et Heure)
            log_entry = {
                "date": datetime.now().strftime("%d/%m/%Y"),
                "heure": datetime.now().strftime("%H:%M"),
                "task": task['name'],
                "weight": weight
            }
            user["history"].append(log_entry)
            
            # Passage de niveau
            while user['xp'] >= get_xp_needed(user['level']):
                user['xp'] -= get_xp_needed(user['level'])
                user['level'] += 1
                st.balloons()
            
            save_data(user)
            st.rerun()
    else:
        c2.write("---")
        c3.button("Fait", key=task['id'], disabled=True, use_container_width=True)

# --- 6. JOURNAL D'ÉPOPÉE ---
st.divider()
with st.expander("📖 Journal d'Épopée (Historique)"):
    if user["history"]:
        for entry in reversed(user["history"]):
            st.write(f"📅 **{entry['date']}** à {entry['heure']} — {entry['task']} (Poids {entry['weight']})")
    else:
        st.write("Aucun exploit enregistré pour le moment.")

with st.sidebar:
    st.header("⚙️ Système")
    if st.button("🔄 Nouvelle Journée"):
        user["completed_today"] = []
        save_data(user)
        st.rerun()
    st.divider()
    st.json(user)
