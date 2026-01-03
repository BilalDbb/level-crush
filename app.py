import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONNEXION ---
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
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            fields = {
                "level": 1, "xp": 0, "mode": "Nomade", 
                "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10},
                "completed_quests": [], "task_diffs": {}, "xp_history": [],
                "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}
            }
            for k, v in fields.items():
                if k not in data: data[k] = v
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Nomade", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, "task_diffs": {}, "xp_history": []}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

user = load_data() if 'user_data' not in st.session_state else st.session_state.user_data

# --- 3. LOGIQUE TITRES ---
TITLES_MAP = {3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 14: "Gardien de Fer", 19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 58: "Commandeur", 66: "Seigneur de Guerre", 75: "Entité Transcendante", 84: "Demi-Dieu", 93: "Souverain de l'Abysse", 100: "LEVEL CRUSHER"}

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="wide")

st.markdown(f"<h1 style='text-align: center; color: #00FFCC;'>⚡ NIV.{user['level']} | {TITLES_MAP.get(user['level'], 'Souverain')}</h1>", unsafe_allow_html=True)

# 4 ONGLETS
tab_quests, tab_stats, tab_titles, tab_config = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "⚙️ Configuration"])

# --- ONGLET 1 : QUÊTES ---
with tab_quests:
    st.info("ℹ️ **Fonctionnement de la Difficulté** : Ajustez le curseur selon l'effort requis. Un poids élevé multiplie vos gains d'XP et de Statistiques, mais augmente proportionnellement la pénalité en cas d'échec (Modes Séide & Exalté).")
    
    for q_type, max_diff in {"Quotidiennes": 3, "Hebdomadaires": 5, "Mensuelles": 7, "Trimestrielles": 9, "Annuelles": 11}.items():
        tasks = user["task_lists"].get(q_type, [])
        if tasks:
            with st.expander(f"{q_type} ({len(tasks)})"):
                for t in tasks:
                    t_id = f"{q_type}_{t}"
                    is_done = t_id in user["completed_quests"]
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"{'✅' if is_done else '🔳'} {t}")
                    
                    current_d = user["task_diffs"].get(t_id, 1)
                    if not is_done:
                        new_d = c2.select_slider("Difficulté", options=list(range(1, max_diff+1)), value=current_d, key=f"sl_{t_id}", label_visibility="collapsed")
                        user["task_diffs"][t_id] = new_d
                        if c3.button("Valider", key=f"btn_{t_id}"):
                            user['xp'] += (100 * new_d)
                            user["completed_quests"].append(t_id)
                            # Log XP pour graphique
                            user["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "xp": (user['level']*1000) + user['xp']})
                            save_data(user); st.rerun()
                    else:
                        c3.button("Fait", key=f"done_{t_id}", disabled=True)

# --- ONGLET 2 : STATISTIQUES ---
with tab_stats:
    col_xy, col_radar = st.columns([2, 1])
    with col_xy:
        st.subheader("📈 Progression")
        if user["xp_history"]:
            df = pd.DataFrame(user["xp_history"])
            fig = go.Figure(go.Scatter(x=df['date'], y=df['xp'], mode='lines+markers', line=dict(color='#00FFCC', width=3)))
            fig.update_layout(template="plotly_dark", xaxis_title="Dates", yaxis_title="XP Cumulée", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("En attente de données de progression...")

    with col_radar:
        st.subheader("🕸️ Profil de Puissance")
        labels = list(user['stats'].keys())
        values = list(user['stats'].values())
        fig_radar = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself', line_color='#00FFCC'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(values)+10])), template="plotly_dark", margin=dict(l=80, r=80, t=40, b=40))
        st.plotly_chart(fig_radar, use_container_width=True)

# --- ONGLET 3 : TITRES ---
with tab_titles:
    st.subheader("🎖️ Arbre des Titres")
    cols = st.columns(4)
    for i, (lvl_req, title) in enumerate(TITLES_MAP.items()):
        unlocked = user['level'] >= lvl_req
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background:{'#1E1E1E' if unlocked else '#0A0A0A'}; border:2px solid {'#00FFCC' if unlocked else '#333'}; padding:15px; border-radius:10px; text-align:center; margin-bottom:15px;">
                <span style="color:{'#00FFCC' if unlocked else '#444'}; font-size:0.8em;">Niveau {lvl_req}</span><br>
                <b style="color:{'white' if unlocked else '#444'}; font-size:1em;">{title if unlocked else '???'}</b>
            </div>
            """, unsafe_allow_html=True)

# --- ONGLET 4 : CONFIGURATION ---
with tab_config:
    st.subheader("🎮 Paramètres")
    help_text = {
        "Nomade": "Mode libre. Aucune pénalité en cas d'échec.",
        "Séide": "Pénalité Miroir active. L'XP descend en cas d'échec, mais votre niveau est protégé.",
        "Exalté": "Hardcore. Pénalité Miroir active. Si l'XP tombe sous zéro, vous perdez un niveau."
    }
    user["mode"] = st.radio("Mode de jeu", ["Nomade", "Séide", "Exalté"], help="Choisissez votre niveau d'engagement.")
    st.write(f"*Description du mode actuel : {help_text[user['mode']]}*")
    
    if st.button("Enregistrer les réglages"): save_data(user); st.success("Configuration sauvegardée.")
    
    st.divider()
    st.subheader("⚙️ Gestionnaire de Quêtes")
    c_p, c_t, c_b = st.columns([1, 2, 1])
    p_choice = c_p.selectbox("Période", list(user["task_lists"].keys()))
    t_name = c_t.text_input("Intitulé de l'objectif")
    if c_b.button("Ajouter"):
        if t_name: user["task_lists"][p_choice].append(t_name); save_data(user); st.rerun()
    
    for p, tasks in user["task_lists"].items():
        if tasks:
            st.markdown(f"**{p}**")
            for t in tasks:
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {t}")
                if cx2.button("❌", key=f"del_{p}_{t}"):
                    user["task_lists"][p].remove(t); save_data(user); st.rerun()

# --- SIDEBAR RESETS ---
with st.sidebar:
    st.header("🔄 Actions de Reset")
    for p in ["Quotidiennes", "Hebdomadaires", "Mensuelles", "Trimestrielles", "Annuelles"]:
        if st.button(f"Réinitialiser {p}"):
            if user["mode"] != "Nomade":
                penalty = 0
                for t in user["task_lists"].get(p, []):
                    if f"{p}_{t}" not in user["completed_quests"]:
                        penalty += (100 * user["task_diffs"].get(f"{p}_{t}", 1))
                if penalty > 0:
                    user["xp"] -= penalty
                    st.error(f"Sanction : -{penalty} XP")
                    if user["mode"] == "Exalté" and user["xp"] < 0:
                        if user["level"] > 1: user["level"] -= 1; user["xp"] = 0
                    elif user["xp"] < 0: user["xp"] = 0
            user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith(p)]
            save_data(user); st.rerun()
