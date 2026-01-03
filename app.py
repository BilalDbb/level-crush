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
    for i in range(20):
        date_str = (start_date + timedelta(days=i*10)).strftime("%Y-%m-%d")
        history.append({"date": date_str, "xp": i * 500})
    return history

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            # Champs obligatoires
            fields = {
                "level": 1, "xp": 0, "mode": "Nomade", 
                "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10},
                "completed_quests": [], "task_diffs": {}, "xp_history": generate_mock_history(),
                "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}
            }
            for k, v in fields.items():
                if k not in data: data[k] = v
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
                        new_d = c2.select_slider("Difficulté", options=list(range(1, max_diff+1)), value=user["task_diffs"].get(t_id, 1), key=f"sl_{t_id}", label_visibility="collapsed")
                        user["task_diffs"][t_id] = new_d
                        if c3.button("Valider", key=f"btn_{t_id}"):
                            user['xp'] += (100 * new_d)
                            user["completed_quests"].append(t_id)
                            user["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": (user['level']*1000) + user['xp']})
                            save_data(user); st.rerun()
                    else:
                        c3.button("Fait", key=f"done_{t_id}", disabled=True)

# --- ONGLET 2 : STATISTIQUES ---
with tab_stats:
    c_xy, c_radar = st.columns([2, 1])
    with c_xy:
        st.subheader("📈 Progression")
        if user["xp_history"]:
            df = pd.DataFrame(user["xp_history"])
            if not df.empty and 'date' in df.columns:
                fig = go.Figure(go.Scatter(x=df['date'], y=df['xp'], mode='lines', line=dict(color='#00FFCC', width=3)))
                fig.update_layout(template="plotly_dark", xaxis_title="Dates", yaxis_title="XP", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
    with c_radar:
        st.subheader("🕸️ Profil de Puissance")
        fig_radar = go.Figure(data=go.Scatterpolar(r=list(user['stats'].values()), theta=list(user['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(user['stats'].values())+10])), template="plotly_dark", margin=dict(l=80, r=80, t=40, b=40))
        st.plotly_chart(fig_radar, use_container_width=True)

# --- ONGLET 3 : TITRES ---
with tab_titles:
    cols = st.columns(4)
    for i, (lvl_req, title) in enumerate(TITLES_MAP.items()):
        unlocked = user['level'] >= lvl_req
        with cols[i % 4]:
            st.markdown(f"<div style='background:{'#1E1E1E' if unlocked else '#0A0A0A'}; border:2px solid {'#00FFCC' if unlocked else '#333'}; padding:15px; border-radius:10px; text-align:center; margin-bottom:15px;'><span style='color:{'#00FFCC' if unlocked else '#444'}; font-size:0.8em;'>Niveau {lvl_req}</span><br><b style='color:{'white' if unlocked else '#444'}; font-size:1em;'>{title if unlocked else '???'}</b></div>", unsafe_allow_html=True)

# --- ONGLET 4 : SYSTÈME ---
with tab_sys:
    st.subheader("🧩 Architecture du Système")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **⚖️ Fonctionnement de la Difficulté (Onglet Quêtes)**
        Ajustez le curseur selon l'effort requis. Un poids élevé multiplie vos gains d'XP et de Statistiques, mais augmente proportionnellement la pénalité en cas d'échec selon le mode de difficulté choisi.
        
        **📈 Gains de base**
        - Quête validée : `100 XP x Difficulté`.
        - Caractéristiques : `+1 point x Difficulté` dans la stat choisie.
        """)
    with c2:
        st.markdown("""
        **🔓 Déblocages & Possibilités**
        - **Accès Immédiat** : Toutes les quêtes (Quotidiennes à Annuelles) sont accessibles dès le Niveau 1.
        - **Évolution de la Capacité** : Tous les 10 Niveaux, vous débloquez la possibilité de rajouter une nouvelle tâche à votre liste.
        """)

# --- ONGLET 5 : CONFIGURATION ---
with tab_config:
    user["mode"] = st.radio("Mode de jeu", ["Nomade", "Séide", "Exalté"], help="Nomade: Zen | Séide: Perte XP | Exalté: De-leveling.")
    if st.button("Enregistrer"): save_data(user); st.rerun()
    st.divider()
    c_p, c_t, c_b = st.columns([1, 2, 1])
    p_choice = c_p.selectbox("Période", list(user["task_lists"].keys()))
    t_name = c_t.text_input("Intitulé")
    if c_b.button("Ajouter"):
        if t_name: user["task_lists"][p_choice].append(t_name); save_data(user); st.rerun()
    for p, tasks in user["task_lists"].items():
        if tasks:
            st.write(f"**{p}**")
            for t in tasks:
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {t}"); (cx2.button("❌", key=f"del_{p}_{t}") and (user["task_lists"][p].remove(t) or save_data(user) or st.rerun()))

with st.sidebar:
    st.header("🔄 Resets")
    for p in user["task_lists"].keys():
        if st.button(f"Reset {p}"):
            # Code de sanction...
            user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith(p)]
            save_data(user); st.rerun()
