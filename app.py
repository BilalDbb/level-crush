import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. CONNEXION SUPABASE ---
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
            if "stats" not in data: data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            if "history" not in data: data["history"] = []
            if "completed_today" not in data: data["completed_today"] = []
            return data
    except: pass
    return {"level": 1, "xp": 0, "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}, "completed_today": [], "history": []}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

user = load_data()

# --- 3. CALCULS ---
def get_xp_needed(lvl):
    exponent = 1.25
    coeff = 200 if lvl < 5 else 25
    xp_palier = int(coeff * (lvl**exponent))
    return xp_palier * 2 if lvl == 100 else xp_palier

def calculate_streak(history):
    if not history: return 0
    dates = sorted(list(set([datetime.strptime(e['date'], "%d/%m/%Y").date() for e in history])), reverse=True)
    streak = 0
    today = datetime.now().date()
    current = today
    
    for d in dates:
        if d == current or d == current - timedelta(days=1):
            streak += 1
            current = d
        else:
            break
    return streak

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="wide")

# --- HUD SUPÉRIEUR ---
xp_target = get_xp_needed(user['level'])
col_info, col_radar = st.columns([1, 1])

with col_info:
    st.title(f"⚡ NIVEAU {user['level']}")
    st.metric("XP ACTUELLE", f"{user['xp']} / {xp_target}")
    st.progress(min(user['xp'] / xp_target, 1.0))
    
    c_s1, c_s2 = st.columns(2)
    c_s1.metric("🔥 STREAK", f"{calculate_streak(user['history'])} Jours")
    c_s2.metric("🏆 TOTAL LOGS", len(user['history']))

with col_radar:
    # Radar Chart avec échelle fixe (0-100)
    categories = list(user['stats'].keys())
    values = list(user['stats'].values())
    fig_radar = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='#00FFCC'))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(max(values)+10, 100)])), showlegend=False, height=300, margin=dict(t=30, b=30, l=30, r=30))
    st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# --- 5. QUÊTES ---
st.subheader("📋 Objectifs du Jour")
daily_tasks = [
    {"id": "t1", "name": "💪 Faire 100 pompes", "def_stat": "Physique"}, 
    {"id": "t2", "name": "🧘 Faire 100 abdos", "def_stat": "Physique"},     
    {"id": "t3", "name": "📖 Lire 20 pages", "def_stat": "Connaissances"},
    {"id": "t4", "name": "🛠️ Rangement / Discipline", "def_stat": "Autonomie"},
]

for task in daily_tasks:
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    is_done = task['id'] in user["completed_today"]
    c1.write(f"{'✅' if is_done else '🔳'} **{task['name']}**")
    if not is_done:
        s = c2.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"], key=f"s_{task['id']}", index=["Physique", "Connaissances", "Autonomie", "Mental"].index(task['def_stat']))
        w = c3.select_slider("Poids", options=[1, 2, 3], key=f"w_{task['id']}")
        if c4.button("Valider", key=task['id'], use_container_width=True):
            user['xp'] += (150 * w)
            user['stats'][s] += w
            user["completed_today"].append(task['id'])
            user["history"].append({"date": datetime.now().strftime("%d/%m/%Y"), "task": task['name'], "stat": s, "weight": w})
            while user['xp'] >= get_xp_needed(user['level']):
                user['xp'] -= get_xp_needed(user['level']); user['level'] += 1; st.balloons()
            save_data(user); st.rerun()
    else:
        c4.button("Fait", key=task['id'], disabled=True, use_container_width=True)

# --- 6. ARCHIVES & ANALYSE XY ---
st.divider()
st.subheader("📈 Analyse de Discipline")

if user["history"]:
    df = pd.DataFrame(user["history"])
    df['date'] = pd.to_datetime(df['date'], format="%d/%m/%Y")
    
    # Filtre par tâche
    task_filter = st.selectbox("Filtrer par objectif :", ["Toutes"] + list(df['task'].unique()))
    plot_df = df if task_filter == "Toutes" else df[df['task'] == task_filter]
    
    # Groupement par jour pour voir la progression
    daily_xp = plot_df.groupby('date').sum(numeric_only=True).reset_index()
    
    # Création du graphique XY (Ligne)
    fig_xy = px.line(daily_xp, x='date', y='weight', title=f"Intensité : {task_filter}", markers=True, line_shape="hv")
    fig_xy.update_traces(line_color='#00FFCC', marker=dict(size=10))
    fig_xy.update_layout(xaxis_title="Date", yaxis_title="Poids cumulé (Intensité)")
    st.plotly_chart(fig_xy, use_container_width=True)
else:
    st.info("Données insuffisantes pour générer le graphique XY.")

with st.sidebar:
    if st.button("🔄 Nouvelle Journée"):
        user["completed_today"] = []; save_data(user); st.rerun()
    st.divider()
    with st.expander("📝 Historique Brut"):
        for e in reversed(user["history"]):
            st.write(f"**{e['date']}** - {e['task']} (+{e['weight']} {e.get('stat', 'N/A')})")
