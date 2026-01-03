import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import random
import time
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
    current_date = datetime(2025, 6, 1)
    xp_acc = 0
    for i in range(50):
        status = random.choice(["fait", "orange", "rouge"])
        gain = random.randint(100, 500) if status != "rouge" else 0
        xp_acc += gain
        history.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "xp": xp_acc,
            "status": status,
            "level_up": True if random.random() > 0.9 else False
        })
        current_date += timedelta(days=2)
    return history

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            # Champs obligatoires
            if "xp_history" not in data or not data["xp_history"]: data["xp_history"] = generate_mock_history()
            if "task_lists" not in data: data["task_lists"] = {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}
            if "level" not in data: data["level"] = 1
            if "xp" not in data: data["xp"] = 0
            if "stats" not in data: data["stats"] = {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}
            if "completed_quests" not in data: data["completed_quests"] = []
            if "task_diffs" not in data: data["task_diffs"] = {}
            if "mode" not in data: data["mode"] = "Nomade"
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Nomade", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, "task_diffs": {}, "xp_history": generate_mock_history()}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()
user = st.session_state.user_data

# --- 3. LOGIQUE TITRES ---
TITLES_MAP = {3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 14: "Gardien de Fer", 19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 58: "Commandeur", 66: "Seigneur de Guerre", 75: "Entité Transcendante", 84: "Demi-Dieu", 93: "Souverain de l'Abysse", 100: "LEVEL CRUSHER"}

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="wide")
st.markdown(f"<h1 style='text-align: center; color: #00FFCC;'>⚡ NIV.{user['level']} | {TITLES_MAP.get(user['level'], 'Souverain')}</h1>", unsafe_allow_html=True)

t_quests, t_stats, t_titles, t_sys, t_config = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "🧩 Système", "⚙️ Configuration"])

# --- QUÊTES ---
with t_quests:
    for q_type, max_d in {"Quotidiennes": 3, "Hebdomadaires": 5, "Mensuelles": 7, "Trimestrielles": 9, "Annuelles": 11}.items():
        tasks = user["task_lists"].get(q_type, [])
        if tasks:
            with st.expander(f"{q_type} ({len(tasks)})", expanded=True):
                for t in tasks:
                    # On crée une clé UNIQUE combinant période et nom
                    clean_id = f"{q_type}_{t}".replace(" ", "_")
                    is_done = clean_id in user["completed_quests"]
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"{'✅' if is_done else '🔳'} {t}")
                    if not is_done:
                        d = c2.select_slider("Difficulté", options=list(range(1, max_d+1)), key=f"sl_{clean_id}", label_visibility="collapsed")
                        if c3.button("Valider", key=f"btn_{clean_id}"):
                            user['xp'] += (100 * d)
                            user["completed_quests"].append(clean_id)
                            user["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": (user['level']*1000)+user['xp'], "status": "fait", "level_up": False})
                            save_data(user); st.rerun()
                    else:
                        c3.button("Fait", key=f"done_{clean_id}", disabled=True)

# --- STATISTIQUES ---
with t_stats:
    c_xy, c_radar = st.columns([2, 1])
    with c_xy:
        st.subheader("📈 Progression")
        df = pd.DataFrame(user["xp_history"])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp'], mode='lines', line=dict(color='#00FFCC', width=3)))
            # Points de couleur OPM
            for s, color in [('rouge', 'red'), ('orange', 'orange')]:
                sub = df[df['status'] == s]
                fig.add_trace(go.Scatter(x=sub['date'], y=sub['xp'], mode='markers', marker=dict(color=color, size=8), showlegend=False))
            st.plotly_chart(fig, use_container_width=True)
    with c_radar:
        st.subheader("🕸️ Profil de Puissance")
        fig_r = go.Figure(data=go.Scatterpolar(r=list(user['stats'].values()), theta=list(user['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(user['stats'].values())+10])), template="plotly_dark")
        st.plotly_chart(fig_r, use_container_width=True)

# --- TITRES ---
with t_titles:
    st.subheader("🎖️ Arbre des Titres")
    cols = st.columns(4)
    for i, (l_req, title) in enumerate(TITLES_MAP.items()):
        unlocked = user['level'] >= l_req
        with cols[i % 4]:
            st.markdown(f"<div style='background:{'#1E1E1E' if unlocked else '#0A0A0A'}; border:2px solid {'#00FFCC' if unlocked else '#333'}; padding:15px; border-radius:10px; text-align:center; margin-bottom:15px;'><span style='color:{'#00FFCC' if unlocked else '#444'}; font-size:0.8em;'>Niveau {l_req}</span><br><b style='color:{'white' if unlocked else '#444'};'>{title if unlocked else '???'}</b></div>", unsafe_allow_html=True)

# --- SYSTÈME ---
with t_sys:
    st.markdown("### 🧩 Architecture du Système")
    st.write("**⚖️ Fonctionnement de la Difficulté (Onglet Quêtes)** : Ajustez le curseur selon l'effort requis. Un poids élevé multiplie vos gains d'XP et de Statistiques, mais augmente proportionnellement la pénalité en cas d'échec selon le mode choisi.")
    st.write("**🔓 Évolution** : Tous les 10 Niveaux, vous pouvez rajouter une nouvelle tâche à votre liste.")

# --- CONFIGURATION ---
with t_config:
    user["mode"] = st.radio("Mode", ["Nomade", "Séide", "Exalté"])
    st.divider()
    c_p, c_t, c_b = st.columns([1, 2, 1])
    p_choice = c_p.selectbox("Période", list(user["task_lists"].keys()))
    t_name = c_t.text_input("Intitulé")
    if c_b.button("Ajouter"):
        if t_name:
            # Sécurité anti-doublon pour Streamlit : on ajoute un timestamp
            unique_task = f"{t_name}" 
            user["task_lists"][p_choice].append(unique_task)
            save_data(user); st.rerun()
    
    for p, tasks in user["task_lists"].items():
        if tasks:
            st.write(f"**{p}**")
            for t in tasks:
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {t}")
                if cx2.button("❌", key=f"del_{p}_{t}_{time.time()}"):
                    user["task_lists"][p].remove(t); save_data(user); st.rerun()

# --- SIDEBAR RESETS ---
with st.sidebar:
    st.header("🔄 Resets")
    for p in user["task_lists"].keys():
        if st.button(f"Réinitialiser {p}", key=f"reset_{p}"):
            user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith(p)]
            save_data(user); st.rerun()
