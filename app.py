import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. CONNEXION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur Cloud : {e}")
    st.stop()

# --- 2. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 

def generate_mock_history():
    history = []
    start_date = datetime(2025, 6, 1)
    end_date = datetime.now()
    current_xp = 0
    current = start_date
    while current <= end_date:
        activity = random.random()
        status = "rouge" if activity < 0.2 else ("orange" if activity < 0.5 else "fait")
        xp_gain = random.randint(50, 400) if status != "rouge" else 0
        current_xp += xp_gain
        history.append({
            "date": current.strftime("%Y-%m-%d"),
            "xp": current_xp,
            "status": status,
            "level_up": True if random.random() > 0.96 else False
        })
        current += timedelta(days=1)
    return history

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            if "xp_history" not in data or len(data["xp_history"]) < 5: data["xp_history"] = generate_mock_history()
            if "stats" not in data: data["stats"] = {"Physique": 20, "Connaissances": 35, "Autonomie": 15, "Mental": 25}
            if "mode" not in data: data["mode"] = "Nomade"
            if "level" not in data: data["level"] = 1
            if "xp" not in data: data["xp"] = 0
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Nomade", "xp_history": generate_mock_history(), "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

# --- 3. LOGIQUE TITRES ---
TITLES_MAP = {3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 14: "Gardien de Fer", 19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 58: "Commandeur", 66: "Seigneur de Guerre", 75: "Entité Transcendante", 84: "Demi-Dieu", 93: "Souverain de l'Abysse", 100: "LEVEL CRUSHER"}

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="wide")

st.markdown(f"<h1 style='text-align: center; color: #00FFCC;'>⚡ NIV.{user['level']} | {TITLES_MAP.get(user['level'], 'Inconnu')}</h1>", unsafe_allow_html=True)

tab_quests, tab_stats, tab_config = st.tabs(["⚔️ Quêtes", "🏆 Titres & Statistiques", "⚙️ Configuration"])

# --- ONGLET 1 : QUÊTES ---
with tab_quests:
    c_q, c_db = st.columns([2, 1])
    with c_q:
        quest_configs = {"Quotidiennes": 3, "Hebdomadaires": 5, "Mensuelles": 7, "Trimestrielles": 9, "Annuelles": 11}
        for q_type, max_w in quest_configs.items():
            tasks = user["task_lists"].get(q_type, [])
            if tasks:
                with st.expander(f"{q_type} ({len(tasks)})"):
                    for t in tasks:
                        t_id = f"{q_type}_{t}"
                        col1, col2, col3 = st.columns([2, 1, 1])
                        col1.write(f"🔳 {t}")
                        w = col2.select_slider("Difficulté", options=list(range(1, max_w+1)), key=f"w_{t_id}", help="Plus la difficulté est haute, plus l'XP et les Stats augmentent.")
                        if col3.button("Valider", key=f"btn_{t_id}"):
                            user['xp'] += (100 * w)
                            save_data(user); st.rerun()
    with c_db:
        st.subheader("💾 JSON de Sauvegarde")
        st.json(user)

# --- ONGLET 2 : TITRES & STATS ---
with tab_stats:
    col_xy, col_radar = st.columns([2, 1])
    with col_xy:
        st.subheader("📈 Progression")
        df = pd.DataFrame(user["xp_history"])
        df['date'] = pd.to_datetime(df['date'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['date'], y=df['xp'], mode='lines', line=dict(color='#00FFCC', width=3)))
        for status, color in [('rouge', 'red'), ('orange', 'orange')]:
            subset = df[df['status'] == status]
            if not subset.empty:
                fig.add_trace(go.Scatter(x=subset['date'], y=subset['xp'], mode='markers', marker=dict(color=color, size=7), showlegend=False))
        lv_up = df[df['level_up'] == True]
        fig.add_trace(go.Scatter(x=lv_up['date'], y=lv_up['xp'], mode='markers', marker=dict(color='black', size=12, line=dict(color='#00FFCC', width=2)), showlegend=False))
        fig.update_layout(template="plotly_dark", xaxis_title="Dates", yaxis_title="XP", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col_radar:
        st.subheader("🕸️ Profil de Puissance")
        labels = list(user['stats'].keys())
        values = list(user['stats'].values())
        fig_radar = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself', line_color='#00FFCC'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(values)+10])), template="plotly_dark", margin=dict(l=60, r=60, t=20, b=20))
        st.plotly_chart(fig_radar, use_container_width=True)

# --- ONGLET 3 : CONFIGURATION ---
with tab_config:
    st.subheader("🎮 Paramètres & Modes")
    help_modes = {
        "Nomade": "Mode libre. Aucune pénalité, tu progresses à ton rythme sans stress.",
        "Séide": "Mode discipliné. Perte d'XP si les tâches ne sont pas faites, mais impossible de perdre un titre acquis.",
        "Exalté": "Mode Hardcore. Perte d'XP massive et De-leveling actif. Tu peux perdre tes titres."
    }
    user["mode"] = st.radio("Mode de jeu", ["Nomade", "Séide", "Exalté"], help=help_modes[user.get("mode", "Nomade")])
    
    st.divider()
    st.subheader("⚙️ Gestionnaire de Quêtes")
    
    # Ajout rapide
    c_cat, c_in, c_bt = st.columns([1, 2, 1])
    new_cat = c_cat.selectbox("Période :", list(user["task_lists"].keys()))
    new_task = c_in.text_input("Nouvel objectif :")
    if c_bt.button("➕ Ajouter", use_container_width=True):
        if new_task: user["task_lists"][new_cat].append(new_task); save_data(user); st.rerun()

    # Liste Globale
    for cat, tasks in user["task_lists"].items():
        if tasks:
            st.markdown(f"**{cat}**")
            for t in tasks:
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {t}")
                if cx2.button("❌", key=f"del_{cat}_{t}"):
                    user["task_lists"][cat].remove(t); save_data(user); st.rerun()

with st.sidebar:
    st.header("⚙️ Système")
    for cat in user["task_lists"].keys():
        if st.button(f"🔄 Reset {cat}"):
            user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith(cat)]
            save_data(user); st.rerun()
