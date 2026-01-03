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
    """Restauration stricte de la logique visuelle SL-118"""
    history = []
    start_date = datetime(2025, 6, 1)
    end_date = datetime.now()
    current_xp = 0
    current = start_date
    while current <= end_date:
        activity = random.random()
        status = "rouge" if activity < 0.2 else ("orange" if activity < 0.5 else "fait")
        xp_gain = random.randint(50, 450) if status != "rouge" else 0
        current_xp += xp_gain
        history.append({
            "date": current.strftime("%Y-%m-%d"),
            "xp": current_xp,
            "status": status,
            "level_up": True if random.random() > 0.97 else False
        })
        current += timedelta(days=1)
    return history

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            if "xp_history" not in data or len(data["xp_history"]) < 10: data["xp_history"] = generate_mock_history()
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Nomade", "xp_history": generate_mock_history(), "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, "task_diffs": {}}

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

t1, t2, t3, t4, t5 = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "🧩 Système", "⚙️ Configuration"])

# --- TAB QUÊTES ---
with t1:
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
                            u['xp'] += (100 * diff)
                            u["completed_quests"].append(t_id)
                            u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": (u['level']*1000)+u['xp'], "status":"fait"})
                            save_data(u); st.rerun()
                    else:
                        c3.button("Fait", key=f"f_{idx}", disabled=True)
                    idx += 1

# --- TAB STATISTIQUES (FIXES & OPM) ---
with t2:
    c_xy, c_rd = st.columns([2, 1])
    with c_xy:
        st.subheader("📈 Progression")
        df = pd.DataFrame(u["xp_history"])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig = go.Figure()
            # Ligne de puissance
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp'], mode='lines', line=dict(color='#00FFCC', width=3)))
            # Points de performance
            for s, color, lab in [('rouge','red', 'Échec'), ('orange','orange', 'Partiel')]:
                sub = df[df['status']==s]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['date'], y=sub['xp'], mode='markers', marker=dict(color=color, size=6), name=lab))
            # Étoiles de Level Up
            lv = df[df.get('level_up', False) == True]
            if not lv.empty:
                fig.add_trace(go.Scatter(x=lv['date'], y=lv['xp'], mode='markers', marker=dict(color='yellow', size=10, symbol='star'), name='LVL UP'))
            
            fig.update_layout(template="plotly_dark", xaxis_title="Dates", yaxis_title="XP", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            # staticPlot=True rend le graphique fixe (non-zoomable, non-cliquable)
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

    with c_rd:
        st.subheader("🕸️ Profil de Puissance")
        fig_r = go.Figure(data=go.Scatterpolar(r=list(u['stats'].values()), theta=list(u['stats'].keys()), fill='toself', line_color='#00FFCC'))
        # Fixation de l'échelle du radar entre 0 et un maximum cohérent
        max_val = max(list(u['stats'].values())) + 20
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max_val])), template="plotly_dark", margin=dict(l=80, r=80, t=40, b=40))
        st.plotly_chart(fig_r, use_container_width=True, config={'staticPlot': True})

# --- TAB TITRES ---
with t3:
    st.subheader("🎖️ Arbre des Titres")
    cols = st.columns(4)
    for i, (l_req, title) in enumerate(TITLES.items()):
        open_t = u['level'] >= l_req
        with cols[i % 4]:
            st.markdown(f"<div style='background:{'#1E1E1E' if open_t else '#0A0A0A'}; border:2px solid {'#00FFCC' if open_t else '#333'}; padding:15px; border-radius:10px; text-align:center; margin-bottom:15px;'><span style='color:{'#00FFCC' if open_t else '#444'}; font-size:0.8em;'>Niveau {l_req}</span><br><b style='color:{'white' if open_t else '#444'};'>{title if open_t else '???'}</b></div>", unsafe_allow_html=True)

# --- TAB CONFIG ---
with t5:
    st.radio("Mode de jeu", ["Nomade", "Séide", "Exalté"], index=["Nomade", "Séide", "Exalté"].index(u["mode"]), key="new_mode", on_change=update_mode)
    st.divider()
    cp, ct, cb = st.columns([1, 2, 1])
    sel_p = cp.selectbox("Période", list(u["task_lists"].keys()))
    name_t = ct.text_input("Intitulé")
    if cb.button("Ajouter"):
        if name_t: u["task_lists"][sel_p].append(name_t); save_data(u); st.rerun()
    for p, tasks in u["task_lists"].items():
        for i, t in enumerate(tasks):
            cx1, cx2 = st.columns([4, 1])
            cx1.write(f"• {t} ({p})")
            if cx2.button("❌", key=f"del_{p}_{i}"):
                u["task_lists"][p].remove(t); save_data(u); st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔄 Resets")
    for p in u["task_lists"].keys():
        if st.button(f"Reset {p}", key=f"rs_{p}"):
            u["completed_quests"] = [q for q in u["completed_quests"] if not q.startswith(p)]
            save_data(u); st.rerun()
