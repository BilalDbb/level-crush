import streamlit as st
import json
import plotly.graph_objects as go
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
            # Initialisations par défaut
            if "stats" not in data:
                data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            if "history" not in data:
                data["history"] = []
            if "completed_today" not in data:
                data["completed_today"] = []
            return data
    except: pass
    return {"level": 1, "xp": 0, "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}, "completed_today": [], "history": []}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

user = load_data()

# --- 3. CALCULS ---
def get_xp_needed(lvl):
    exponent = 1.25 #
    coeff = 200 if lvl < 5 else 25 #
    xp_palier = int(coeff * (lvl**exponent))
    return xp_palier * 2 if lvl == 100 else xp_palier

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="wide")
st.title("⚡ LEVEL CRUSH : ÉTAT DE PUISSANCE")

# --- HUD SUPÉRIEUR ---
xp_target = get_xp_needed(user['level'])
col_info, col_graph = st.columns([1, 1])

with col_info:
    st.header(f"NIVEAU {user['level']}")
    st.metric("XP Totale", f"{user['xp']} / {xp_target}")
    st.progress(min(user['xp'] / xp_target, 1.0))
    
    st.write("### 📊 Statistiques")
    for stat, val in user['stats'].items():
        st.write(f"**{stat}** : {val}")

with col_graph:
    # --- GRAPHIQUE RADAR (STYLE ONE PUNCH MAN) ---
    categories = list(user['stats'].keys())
    values = list(user['stats'].values())
    
    # On ferme le cercle en répétant la première valeur
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        line_color='#00FFCC',
        fillcolor='rgba(0, 255, 204, 0.3)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, showticklabels=False)),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 5. SYSTÈME DE QUÊTES (FLUIDE) ---
st.subheader("📋 Objectifs Personnalisables")

BASE_XP = 150 #
tasks_config = [
    {"id": "task1", "name": "💪 Faire 100 pompes"}, 
    {"id": "task2", "name": "🧘 Faire 100 abdos"},     
    {"id": "task3", "name": "📖 Lire 20 pages"},
    {"id": "task4", "name": "🛠️ Rangement / Discipline"},
]

for task in tasks_config:
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    is_done = task['id'] in user["completed_today"]
    
    c1.write(f"{'✅' if is_done else '🔳'} **{task['name']}**")
    
    if not is_done:
        # L'utilisateur lie lui-même la caractéristique et le poids
        chosen_stat = c2.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"], key=f"s_{task['id']}")
        weight = c3.select_slider("Poids", options=[1, 2, 3], key=f"w_{task['id']}")
        
        if c4.button("Valider", key=task['id'], use_container_width=True):
            gain = BASE_XP * weight
            user['xp'] += gain
            user['stats'][chosen_stat] += weight
            user["completed_today"].append(task['id'])
            
            # Historique
            user["history"].append({
                "date": datetime.now().strftime("%d/%m/%Y"),
                "task": task['name'],
                "stat": chosen_stat,
                "weight": weight
            })
            
            # Level UP
            while user['xp'] >= get_xp_needed(user['level']):
                user['xp'] -= get_xp_needed(user['level'])
                user['level'] += 1
                st.balloons()
            
            save_data(user)
            st.rerun()
    else:
        c2.empty()
        c3.empty()
        c4.button("Fait", key=task['id'], disabled=True, use_container_width=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Système")
    if st.button("🔄 Nouvelle Journée"):
        user["completed_today"] = []
        save_data(user)
        st.rerun()
    st.divider()
    with st.expander("📖 Journal"):
        for entry in reversed(user["history"]):
            st.write(f"**{entry['date']}** : {entry['task']} (+{entry['weight']} {entry['stat']})")
