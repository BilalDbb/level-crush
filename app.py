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
            # Initialisation si nouvelles clés manquantes
            if "stats" not in data:
                data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            if "last_reset" not in data:
                data["last_reset"] = datetime.now().strftime("%Y-%m-%d")
            if "completed_today" not in data:
                data["completed_today"] = []
            return data
    except: pass
    return {
        "level": 1, "xp": 0, 
        "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0},
        "last_reset": datetime.now().strftime("%Y-%m-%d"),
        "completed_today": []
    }

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

# --- 3. GESTION DU TEMPS (RESET AUTO) ---
user = load_data()
today = datetime.now().strftime("%Y-%m-%d")

if user["last_reset"] != today:
    user["completed_today"] = []
    user["last_reset"] = today
    save_data(user)

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
col1.metric("NIVEAU", user['level'])
col2.metric("XP", f"{user['xp']} / {xp_target}")
st.progress(min(user['xp'] / xp_target, 1.0))

# STATS
st.write("### 📊 Caractéristiques")
s_col = st.columns(4)
stats_keys = list(user['stats'].keys())
for i in range(4):
    s_col[i].metric(stats_keys[i][:3], user['stats'][stats_keys[i]])

st.divider()

# --- SYSTÈME DE QUÊTES (4 SLOTS) ---
st.subheader("📋 Objectifs du Jour")

BASE_XP = 150 
daily_tasks = [
    {"id": "pushups", "name": "💪 Faire 100 pompes", "weight": 3, "stat": "Physique"}, 
    {"id": "abs", "name": "🧘 Faire 100 abdos", "weight": 2, "stat": "Physique"},     
    {"id": "read", "name": "📖 Lire 20 pages", "weight": 2, "stat": "Connaissances"},
    {"id": "clean", "name": "🛠️ Rangement / Autonomie", "weight": 1, "stat": "Autonomie"},
]

for task in daily_tasks:
    c1, c2 = st.columns([3, 1])
    is_done = task['id'] in user["completed_today"]
    gain_xp = BASE_XP * task['weight']
    
    status_icon = "✅" if is_done else "🔳"
    c1.write(f"{status_icon} **{task['name']}**")
    c1.caption(f"+{gain_xp} XP | +{task['weight']} {task['stat']}")
    
    if not is_done:
        if c2.button("Valider", key=task['id'], use_container_width=True):
            user['xp'] += gain_xp
            user['stats'][task['stat']] += task['weight']
            user["completed_today"].append(task['id'])
            
            while user['xp'] >= get_xp_needed(user['level']):
                user['xp'] -= get_xp_needed(user['level'])
                user['level'] += 1
                st.balloons()
            
            save_data(user)
            st.rerun()
    else:
        c2.button("Fait", key=task['id'], disabled=True, use_container_width=True)

with st.sidebar:
    st.write("Dernier Reset :", user["last_reset"])
    if st.button("🔄 Reset Manuel"):
        user["completed_today"] = []
        save_data(user)
        st.rerun()
    st.divider()
    st.json(user)
