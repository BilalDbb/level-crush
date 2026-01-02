import streamlit as st
import json
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
            # Initialisation des stats si elles n'existent pas encore dans ta base
            if "stats" not in data:
                data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            return data
    except: pass
    return {"level": 1, "xp": 0, "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

# --- 3. SESSION ---
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

if 'completed_quests' not in st.session_state:
    st.session_state.completed_quests = []

# --- 4. CALCULS ---
def get_xp_needed(lvl):
    exponent = 1.25 
    coeff = 200 if lvl < 5 else 25
    xp_palier = int(coeff * (lvl**exponent))
    return xp_palier * 2 if lvl == 100 else xp_palier

# --- 5. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")
st.title("⚡ LEVEL CRUSH : SYSTÈME DE STATS")

xp_target = get_xp_needed(user['level'])

# --- HUD PRINCIPAL ---
col1, col2 = st.columns(2)
col1.metric("NIVEAU GLOBAL", user['level'])
col2.metric("XP", f"{user['xp']} / {xp_target}")
st.progress(min(user['xp'] / xp_target, 1.0))

# --- AFFICHAGE DES CARACTÉRISTIQUES ---
st.write("### 📊 Caractéristiques")
s_col1, s_col2, s_col3, s_col4 = st.columns(4)
s_col1.metric("💪 Phy", user['stats']['Physique'])
s_col2.metric("🧠 Con", user['stats']['Connaissances'])
s_col3.metric("🛠️ Aut", user['stats']['Autonomie'])
s_col4.metric("🧘 Men", user['stats']['Mental'])

st.divider()

# --- SYSTÈME DE QUÊTES ---
st.subheader("📋 Objectifs du Jour")

BASE_XP = 150 
# Ici, on lie chaque tâche à une caractéristique spécifique
daily_tasks = [
    {"id": "pushups", "name": "💪 Faire 100 pompes", "weight": 3, "stat": "Physique"}, 
    {"id": "abs", "name": "🧘 Faire 100 abdos", "weight": 2, "stat": "Physique"},     
    {"id": "read", "name": "📖 Lire 20 pages", "weight": 1, "stat": "Connaissances"},      
]

for task in daily_tasks:
    c1, c2 = st.columns([3, 1])
    is_done = task['id'] in st.session_state.completed_quests
    gain_xp = BASE_XP * task['weight']
    
    status_icon = "✅" if is_done else "🔳"
    c1.write(f"{status_icon} **{task['name']}**")
    c1.caption(f"Gain : +{gain_xp} XP | Stat : +{task['weight']} {task['stat']}")
    
    if not is_done:
        if c2.button("Valider", key=task['id'], use_container_width=True):
            # 1. Augmenter l'XP globale
            user['xp'] += gain_xp
            # 2. Augmenter la Statistique associée
            user['stats'][task['stat']] += task['weight']
            
            st.session_state.completed_quests.append(task['id'])
            
            # Boucle de niveau
            while user['xp'] >= get_xp_needed(user['level']):
                user['xp'] -= get_xp_needed(user['level'])
                user['level'] += 1
                st.balloons()
            
            save_data(user)
            st.rerun()
    else:
        c2.button("Fait", key=task['
