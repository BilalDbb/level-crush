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

# --- 2. GESTION DES DONNÉES & COURBE ---
MY_ID = "shadow_monarch_01" 

def get_xp_required(lvl):
    """Formule : coef * (prochain_niveau ^ 1.2)"""
    next_lvl = lvl + 1
    if lvl < 5:
        return int(200 * (next_lvl**1.2))
    elif 5 <= lvl < 100:
        return int(25 * (next_lvl**1.2))
    else: # Niveau 100 (Pic final)
        return int(get_xp_required(99) * 10)

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            fields = {"level": 1, "xp": 0, "mode": "Nomade", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, "xp_history": []}
            for k, v in fields.items():
                if k not in data: data[k] = v
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Nomade", "xp_history": [], "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()
u = st.session_state.user_data

def process_xp_change(amount):
    """Gestion intelligente des gains et pertes avec changement de niveau"""
    u['xp'] += amount
    # Gestion Level UP
    while True:
        req = get_xp_required(u['level'])
        if u['xp'] >= req and u['level'] < 100:
            u['xp'] -= req
            u['level'] += 1
            st.toast("🌟 LEVEL UP !")
        else: break
    # Gestion Level DOWN
    while u['xp'] < 0 and u['level'] > 1:
        u['level'] -= 1
        u['xp'] += get_xp_required(u['level'])
        st.toast("⚠️ LEVEL DOWN...", icon="📉")
    if u['level'] == 1 and u['xp'] < 0: u['xp'] = 0

# --- 4. INTERFACE ---
TITLES = {1: "Soldat Rang E", 3: "Néophyte", 10: "Soldat de Plomb", 30: "Chevalier d'Acier", 50: "Légat du Système", 100: "LEVEL CRUSHER"}
def get_title(lvl):
    unlocked = [t for l, t in TITLES.items() if l <= lvl]
    return unlocked[-1] if unlocked else "Inconnu"

st.set_page_config(page_title="LEVEL CRUSH", layout="wide")
st.markdown(f"<h1 style='text-align:center; color:#00FFCC;'>⚡ NIV.{u['level']} | {get_title(u['level'])}</h1>", unsafe_allow_html=True)

tabs = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "🧩 Système", "⚙️ Configuration"])

# --- TAB QUÊTES ---
with tabs[0]:
    req = get_xp_required(u['level'])
    st.subheader(f"🚀 Progression : {u['xp']} / {req} XP")
    st.progress(min(u['xp']/req, 1.0))
    st.divider()
    
    idx = 0
    for q_p, m_d in {"Quotidiennes":3, "Hebdomadaires":5, "Mensuelles":7, "Trimestrielles":9, "Annuelles":11}.items():
        tasks = u["task_lists"].get(q_p, [])
        if tasks:
            with st.expander(f"{q_p} ({len(tasks)})", expanded=True):
                for task in tasks:
                    t_id = f"{q_p}_{task}"
                    done = t_id in u["completed_quests"]
                    c1, c2, c3, c4 = st.columns([2, 1, 0.5, 0.5])
                    c1.write(f"{'✅' if done else '🔳'} {task}")
                    if not done:
                        diff = c2.select_slider("Diff", options=list(range(1, m_d+1)), key=f"s_{idx}", label_visibility="collapsed")
                        if c3.button("✔️", key=f"v_{idx}"):
                            process_xp_change(100 * diff)
                            u["completed_quests"].append(t_id)
                            u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": u['xp'], "status":"fait"})
                            save_data(u); st.rerun()
                        if u['mode'] != "Nomade":
                            if c4.button("❌", key=f"x_{idx}"):
                                process_xp_change(-(100 * diff))
                                u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "xp": u['xp'], "status":"rouge"})
                                save_data(u); st.rerun()
                    idx += 1

# --- TAB STATISTIQUES ---
with tabs[1]:
    c_xy, c_rd = st.columns([1.2, 1])
    with c_xy:
        df = pd.DataFrame(u["xp_history"])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp'], mode='lines+markers', line=dict(color='#00FFCC'), name="Historique XP"))
            fig.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    with c_rd:
        fig_r = go.Figure(data=go.Scatterpolar(r=list(u['stats'].values()), theta=list(u['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(u['stats'].values())+15])), template="plotly_dark", height=400)
        st.plotly_chart(fig_r, use_container_width=True)

# --- TAB CONFIGURATION ---
with tabs[4]:
    new_m = st.radio("Mode de Jeu", ["Nomade", "Séide", "Exalté"], index=["Nomade", "Séide", "Exalté"].index(u["mode"]))
    if new_m != u["mode"]:
        u["mode"] = new_m
        save_data(u); st.rerun()
    st.divider()
    cp, ct, cb = st.columns([1, 2, 1])
    sel_p = cp.selectbox("Période", list(u["task_lists"].keys()))
    name_t = ct.text_input("Ajouter une tâche")
    if cb.button("Ajouter"):
        if name_t: u["task_lists"][sel_p].append(name_t); save_data(u); st.rerun()

# --- SIDEBAR (RESETS & SIMULATION) ---
with st.sidebar:
    st.header("⏳ Simulation Temporelle")
    if st.button("⏭️ SAUTER UN JOUR", use_container_width=True, help="Simule la fin de journée sans quêtes faites"):
        penalty = 0
        if u['mode'] == "Séide": penalty = -100
        elif u['mode'] == "Exalté":
            # Pénalité = -100 XP par quête quotidienne non faite (ou -500 par défaut)
            daily_count = len(u["task_lists"].get("Quotidiennes", []))
            penalty = -(daily_count * 100) if daily_count > 0 else -500
        
        process_xp_change(penalty)
        u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": u['xp'], "status":"rouge"})
        u["completed_quests"] = [q for q in u["completed_quests"] if not q.startswith("Quotidiennes")]
        save_data(u)
        st.warning(f"Jour sauté ! Pénalité subie : {penalty} XP")
        st.rerun()

    st.header("🔄 Réinitialisations")
    for p in u["task_lists"].keys():
        if st.button(f"Reset {p}", key=f"rs_{p}"):
            u["completed_quests"] = [q for q in u["completed_quests"] if not q.startswith(p)]
            save_data(u); st.rerun()
