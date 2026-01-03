import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. CONNEXION SUPABASE ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur Cloud : {e}")
    st.stop()

# --- 2. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 

def generate_mock_history():
    history = []
    curr = datetime(2025, 6, 1)
    xp_acc = 0
    while curr <= datetime.now():
        activity = random.random()
        status = "rouge" if activity < 0.2 else ("orange" if activity < 0.5 else "fait")
        xp_acc += random.randint(100, 500) if status != "rouge" else 0
        history.append({
            "date": curr.strftime("%Y-%m-%d"),
            "xp": xp_acc,
            "status": status,
            "level_up": True if random.random() > 0.95 else False
        })
        curr += timedelta(days=2)
    return history

def load_data():
    try:
        res = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if res.data:
            d = res.data[0]['data']
            if isinstance(d, str): d = json.loads(d)
            # Garanties structurelles
            for k, v in {"level":1, "xp":0, "mode":"Nomade", "stats":{"Physique":10,"Connaissances":10,"Autonomie":10,"Mental":10}, "completed_quests":[], "task_lists":{"Quotidiennes":[],"Hebdomadaires":[],"Mensuelles":[],"Trimestrielles":[],"Annuelles":[]}, "task_diffs":{}, "xp_history":[]}.items():
                if k not in d: d[k] = v
            if not d["xp_history"]: d["xp_history"] = generate_mock_history()
            return d
    except: pass
    return {"level":1, "xp":0, "mode":"Nomade", "stats":{"Physique":10,"Connaissances":10,"Autonomie":10,"Mental":10}, "completed_quests":[], "task_lists":{"Quotidiennes":[],"Hebdomadaires":[],"Mensuelles":[],"Trimestrielles":[],"Annuelles":[]}, "task_diffs":{}, "xp_history":generate_mock_history()}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

def update_mode():
    st.session_state.user_data["mode"] = st.session_state.new_mode
    save_data(st.session_state.user_data)
    st.toast(f"Mode {st.session_state.new_mode} activé !")

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()
u = st.session_state.user_data

# --- 3. TITRES ---
TITLES = {1: "Soldat de Rang E", 3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 14: "Gardien de Fer", 19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 58: "Commandeur", 66: "Seigneur de Guerre", 75: "Entité Transcendante", 84: "Demi-Dieu", 93: "Souverain de l'Abysse", 100: "LEVEL CRUSHER"}

def get_current_title(lvl):
    unlocked = [t for l, t in TITLES.items() if l <= lvl]
    return unlocked[-1] if unlocked else "Inconnu"

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", layout="wide")
st.markdown(f"<h1 style='text-align:center; color:#00FFCC;'>⚡ NIV.{u['level']} | {get_current_title(u['level'])}</h1>", unsafe_allow_html=True)

tabs = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "🧩 Système", "⚙️ Configuration"])

# --- QUÊTES ---
with tabs[0]:
    for q_p, m_d in {"Quotidiennes":3, "Hebdomadaires":5, "Mensuelles":7, "Trimestrielles":9, "Annuelles":11}.items():
        list_t = u["task_lists"].get(q_p, [])
        if list_t:
            with st.expander(f"{q_p} ({len(list_t)})", expanded=True):
                for i, task in enumerate(list_t):
                    t_key = f"{q_p}_{task}"
                    done = t_key in u["completed_quests"]
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"{'✅' if done else '🔳'} {task}")
                    if not done:
                        diff = c2.select_slider("Difficulté", options=list(range(1, m_d+1)), key=f"s_{q_p}_{i}", label_visibility="collapsed")
                        if c3.button("Valider", key=f"b_{q_p}_{i}"):
                            u['xp'] += (100 * diff)
                            u["completed_quests"].append(t_key)
                            u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": (u['level']*1000)+u['xp'], "status":"fait"})
                            save_data(u); st.rerun()
                    else:
                        c3.button("Fait", key=f"f_{q_p}_{i}", disabled=True)

# --- STATISTIQUES ---
with tabs[1]:
    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.subheader("📈 Progression")
        df = pd.DataFrame(u["xp_history"])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp'], mode='lines', line=dict(color='#00FFCC', width=3), name="Courbe XP"))
            for s, color, lab in [('rouge','red', 'Échec'), ('orange','orange', 'Partiel'), ('fait','#00FFCC', 'Succès')]:
                sub = df[df['status']==s]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['date'], y=sub['xp'], mode='markers', marker=dict(color=color, size=6), name=lab))
            fig.update_layout(template="plotly_dark", height=400, xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_right:
        st.subheader("🕸️ Profil de Puissance")
        fig_r = go.Figure(data=go.Scatterpolar(r=list(u['stats'].values()), theta=list(u['stats'].keys()), fill='toself', line_color='#00FFCC'))
        m_val = max(list(u['stats'].values())) + 15
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, m_val], fixedrange=True)), template="plotly_dark", height=400, margin=dict(l=50, r=50, t=40, b=40))
        st.plotly_chart(fig_r, use_container_width=True, config={'staticPlot': True})

# --- TITRES ---
with tabs[2]:
    st.subheader("🎖️ Arbre des Titres")
    cols = st.columns(4)
    for i, (l_req, title) in enumerate(TITLES.items()):
        unlocked = u['level'] >= l_req
        with cols[i % 4]:
            st.markdown(f"<div style='background:{'#1E1E1E' if unlocked else '#0A0A0A'}; border:2px solid {'#00FFCC' if unlocked else '#333'}; padding:15px; border-radius:10px; text-align:center; margin-bottom:15px;'><span style='color:{'#00FFCC' if unlocked else '#444'}; font-size:0.8em;'>Niveau {l_req}</span><br><b style='color:{'white' if unlocked else '#444'};'>{title if unlocked else '???'}</b></div>", unsafe_allow_html=True)

# --- SYSTÈME ---
with tabs[3]:
    st.subheader("🧩 Règles")
    st.write("**Difficulté (Onglet Quêtes)** : Gains = 100 XP x Diff. Pénalité miroir selon le mode.")
    st.write("**Capacité** : Toutes quêtes dès Niv. 1. +1 tâche possible tous les 10 niveaux.")

# --- CONFIGURATION ---
with tabs[4]:
    st.radio("Mode de jeu", ["Nomade", "Séide", "Exalté"], index=["Nomade", "Séide", "Exalté"].index(u["mode"]), key="new_mode", on_change=update_mode)
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    p_sel = c1.selectbox("Période", list(u["task_lists"].keys()))
    t_add = c2.text_input("Intitulé")
    if c3.button("Ajouter"):
        if t_add: u["task_lists"][p_sel].append(t_add); save_data(u); st.rerun()
    for p, tasks in u["task_lists"].items():
        if tasks:
            st.write(f"**{p}**")
            for i, t in enumerate(tasks):
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {t}")
                if cx2.button("❌", key=f"del_{p}_{i}"):
                    u["task_lists"][p].remove(t); save_data(u); st.rerun()

# --- SIDEBAR (TOUJOURS VISIBLE) ---
with st.sidebar:
    st.header("🔄 Resets")
    for p in ["Quotidiennes", "Hebdomadaires", "Mensuelles", "Trimestrielles", "Annuelles"]:
        if st.button(f"Réinitialiser {p}", key=f"rs_side_{p}"):
            u["completed_quests"] = [q for q in u["completed_quests"] if not q.startswith(p)]
            save_data(u); st.rerun()
