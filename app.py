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
    """Génère un historique OPM Style depuis juin 2025"""
    history = []
    start_date = datetime(2025, 6, 1)
    end_date = datetime.now()
    current_xp = 0
    current = start_date
    while current <= end_date:
        activity = random.random()
        status = "rouge" if activity < 0.2 else ("orange" if activity < 0.5 else "fait")
        xp_gain = random.randint(100, 600) if status != "rouge" else 0
        current_xp += xp_gain
        history.append({
            "date": current.strftime("%Y-%m-%d"),
            "xp": current_xp,
            "status": status,
            "level_up": True if random.random() > 0.95 else False
        })
        current += timedelta(days=1)
    return history

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            # Garantir les champs
            fields = {"level": 1, "xp": 0, "mode": "Nomade", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_diffs": {}, "xp_history": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}}
            for k, v in fields.items():
                if k not in data: data[k] = v
            if not data["xp_history"]: data["xp_history"] = generate_mock_history()
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

tab_quests, tab_stats, tab_titles, tab_sys, tab_config = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "🧩 Système", "⚙️ Configuration"])

# --- ONGLET 1 : QUÊTES ---
with tab_quests:
    for q_type, max_diff in {"Quotidiennes": 3, "Hebdomadaires": 5, "Mensuelles": 7, "Trimestrielles": 9, "Annuelles": 11}.items():
        tasks = user["task_lists"].get(q_type, [])
        if tasks:
            with st.expander(f"{q_type} ({len(tasks)})"):
                for t in tasks:
                    t_id = f"{q_type}_{t}"
                    is_done = t_id in user["completed_quests"]
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"{'✅' if is_done else '🔳'} {t}")
                    if not is_done:
                        d = c2.select_slider("Difficulté", options=list(range(1, max_diff+1)), value=user["task_diffs"].get(t_id, 1), key=f"sl_{t_id}", label_visibility="collapsed")
                        user["task_diffs"][t_id] = d
                        if c3.button("Valider", key=f"btn_{t_id}"):
                            user['xp'] += (100 * d)
                            user["completed_quests"].append(t_id)
                            user["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": (user['level']*1000) + user['xp'], "status": "fait", "level_up": False})
                            save_data(user); st.rerun()
                    else:
                        c3.button("Fait", key=f"done_{t_id}", disabled=True)

# --- ONGLET 2 : STATISTIQUES (STYLE OPM RESTAURÉ) ---
with tab_stats:
    c_xy, c_radar = st.columns([2, 1])
    with c_xy:
        st.subheader("📈 Progression")
        df = pd.DataFrame(user["xp_history"])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            fig = go.Figure()
            # Ligne de base
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp'], mode='lines', line=dict(color='#00FFCC', width=2), name='XP'))
            # Points indicateurs
            for status, color, name in [('rouge', 'red', 'Échec'), ('orange', 'orange', 'Partiel')]:
                sub = df[df['status'] == status]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['date'], y=sub['xp'], mode='markers', marker=dict(color=color, size=6), name=name))
            # Level Up
            lv = df[df['level_up'] == True]
            if not lv.empty:
                fig.add_trace(go.Scatter(x=lv['date'], y=lv['xp'], mode='markers', marker=dict(color='black', size=10, symbol='star', line=dict(color='#00FFCC', width=1)), name='LEVEL UP'))
            
            fig.update_layout(template="plotly_dark", xaxis_title="Dates", yaxis_title="XP", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
    with c_radar:
        st.subheader("🕸️ Profil de Puissance")
        fig_r = go.Figure(data=go.Scatterpolar(r=list(user['stats'].values()), theta=list(user['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(user['stats'].values())+10])), template="plotly_dark", margin=dict(l=80, r=80, t=40, b=40))
        st.plotly_chart(fig_r, use_container_width=True)

# --- ONGLET 4 : SYSTÈME ---
with tab_sys:
    st.subheader("🧩 Architecture du Système")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**⚖️ Fonctionnement de la Difficulté (Onglet Quêtes)**")
        st.write("Ajustez le curseur selon l'effort requis. Un poids élevé multiplie vos gains d'XP et de Statistiques, mais augmente proportionnellement la pénalité en cas d'échec selon le mode de difficulté choisi.")
    with c2:
        st.markdown("**🔓 Déblocages & Possibilités**")
        st.write("- **Accès Immédiat** : Toutes les quêtes sont accessibles dès le Niveau 1.")
        st.write("- **Évolution** : Tous les 10 Niveaux, vous pouvez rajouter une nouvelle tâche à votre liste.")

# --- ONGLET 5 : CONFIGURATION (FIX FALSE) ---
with tab_config:
    user["mode"] = st.radio("Mode", ["Nomade", "Séide", "Exalté"], help="Nomade: Zen | Séide: Perte XP | Exalté: De-leveling.")
    if st.button("Sauvegarder"): save_data(user); st.rerun()
    st.divider()
    cp, ct, cb = st.columns([1, 2, 1])
    p = cp.selectbox("Période", list(user["task_lists"].keys()))
    t_name = ct.text_input("Intitulé")
    if cb.button("Ajouter"):
        if t_name: user["task_lists"][p].append(t_name); save_data(user); st.rerun()
    
    for cat, t_list in user["task_lists"].items():
        if t_list:
            st.write(f"**{cat}**")
            for task in t_list:
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {task}")
                if cx2.button("❌", key=f"del_{cat}_{task}"):
                    user["task_lists"][cat].remove(task)
                    save_data(user)
                    st.rerun()

with st.sidebar:
    st.header("🔄 Resets")
    for p in user["task_lists"].keys():
        if st.button(f"Reset {p}"):
            user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith(p)]
            save_data(user); st.rerun()
