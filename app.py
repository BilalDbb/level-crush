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
        history.append({"date": curr.strftime("%Y-%m-%d"), "xp": xp_acc, "status": status})
        curr += timedelta(days=2)
    return history

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            # Garanties structurelles
            for k, v in {"level": 1, "xp": 0, "mode": "Nomade", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, "xp_history": []}.items():
                if k not in data: data[k] = v
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Nomade", "xp_history": generate_mock_history(), "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

def update_mode():
    st.session_state.user_data["mode"] = st.session_state.new_mode
    save_data(st.session_state.user_data)
    st.toast(f"Mode {st.session_state.new_mode} activé !")

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()
u = st.session_state.user_data

# --- 3. LOGIQUE SYSTÈME ---
TITLES = {1: "Soldat de Rang E", 3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 14: "Gardien de Fer", 19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 100: "LEVEL CRUSHER"}

def get_current_title(lvl):
    unlocked = [t for l, t in TITLES.items() if l <= lvl]
    return unlocked[-1] if unlocked else "Inconnu"

def process_xp_change(amount):
    """Gère le gain/perte d'XP avec report (Carry-over)"""
    u['xp'] += amount
    xp_palier = u['level'] * 1000
    
    # Gestion du Level Up (Surplus ajouté au suivant)
    while u['xp'] >= xp_palier:
        u['xp'] -= xp_palier
        u['level'] += 1
        xp_palier = u['level'] * 1000
        st.balloons()
        
    # Gestion du Level Down (Déficit retiré du précédent)
    while u['xp'] < 0 and u['level'] > 1:
        u['level'] -= 1
        xp_palier_prev = u['level'] * 1000
        u['xp'] += xp_palier_prev
    
    if u['level'] == 1 and u['xp'] < 0: u['xp'] = 0

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", layout="wide")
st.markdown(f"<h1 style='text-align:center; color:#00FFCC;'>⚡ NIV.{u['level']} | {get_current_title(u['level'])}</h1>", unsafe_allow_html=True)

tabs = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "🧩 Système", "⚙️ Configuration"])

# --- TAB QUÊTES ---
with tabs[0]:
    xp_palier = u['level'] * 1000
    prog = min(max(u['xp'] / xp_palier, 0.0), 1.0)
    st.subheader(f"🚀 Progression vers Niv.{u['level'] + 1}")
    c_b, c_v = st.columns([4, 1])
    c_b.progress(prog)
    c_v.write(f"**{u['xp']} / {xp_palier} XP**")
    st.divider()
    
    idx = 0
    for q_p, m_d in {"Quotidiennes":3, "Hebdomadaires":5, "Mensuelles":7, "Trimestrielles":9, "Annuelles":11}.items():
        tasks = u["task_lists"].get(q_p, [])
        if tasks:
            with st.expander(f"{q_p} ({len(tasks)})", expanded=True):
                for task in tasks:
                    t_id = f"{q_p}_{task}"
                    done = t_id in u["completed_quests"]
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"{'✅' if done else '🔳'} {task}")
                    if not done:
                        diff = c2.select_slider("Diff", options=list(range(1, m_d+1)), key=f"s_{idx}", label_visibility="collapsed")
                        if c3.button("Valider", key=f"b_{idx}"):
                            gain = 100 * diff
                            process_xp_change(gain)
                            u["completed_quests"].append(t_id)
                            u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": (u['level']*1000)+u['xp'], "status":"fait"})
                            save_data(u); st.rerun()
                    else:
                        c3.button("Fait", key=f"f_{idx}", disabled=True)
                    idx += 1

# --- TAB STATISTIQUES ---
with tabs[1]:
    c_xy, c_rd = st.columns([1.2, 1])
    with c_xy:
        df = pd.DataFrame(u["xp_history"])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp'], mode='lines', line=dict(color='#00FFCC', width=3), name="XP Totale"))
            for s, color, lab in [('rouge','red', 'Échec'), ('orange','orange', 'Partiel'), ('fait','#00FFCC', 'Succès')]:
                sub = df[df['status']==s]
                if not sub.empty: fig.add_trace(go.Scatter(x=sub['date'], y=sub['xp'], mode='markers', marker=dict(color=color, size=6), name=lab))
            fig.update_layout(template="plotly_dark", height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    with c_rd:
        fig_r = go.Figure(data=go.Scatterpolar(r=list(u['stats'].values()), theta=list(u['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(u['stats'].values())+15])), template="plotly_dark", height=400)
        st.plotly_chart(fig_r, use_container_width=True)

# --- TAB CONFIGURATION ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔄 Resets")
    for p in u["task_lists"].keys():
        if st.button(f"Reset {p}", key=f"rs_{p}"):
            u["completed_quests"] = [q for q in u["completed_quests"] if not q.startswith(p)]
            # Si mode Exalté : échec du reset = pénalité
            if u['mode'] == "Exalté": process_xp_change(-500)
            save_data(u); st.rerun()
