import streamlit as st
import json
import pandas as pd
import plotly.express as px
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
        if response.data and len(response.data) > 0:
            raw_data = response.data[0]['data']
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            # Initialisations Sécurité
            if "mode" not in data: data["mode"] = "Nomade"
            if "xp_history" not in data: data["xp_history"] = []
            if "task_lists" not in data: 
                data["task_lists"] = {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}
            if "stats" not in data: data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            if "completed_quests" not in data: data["completed_quests"] = []
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Nomade", "xp_history": [], "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

# --- 3. LOGIQUE TITRES ---
TITLES_MAP = {
    3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 14: "Gardien de Fer", 
    19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 
    36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 
    58: "Commandeur", 66: "Seigneur de Guerre", 75: "Entité Transcendante", 
    84: "Demi-Dieu", 93: "Souverain de l'Abysse", 100: "LEVEL CRUSHER"
}

def get_current_title(lvl):
    unlocked = [t for l, t in TITLES_MAP.items() if lvl >= l]
    return unlocked[-1] if unlocked else "Sans Titre"

def get_xp_needed(lvl):
    exponent = 1.25 
    coeff = 200 if lvl < 5 else 25 
    return int(coeff * (lvl**exponent))

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="wide")

xp_target = get_xp_needed(user['level'])

# HEADER
st.title(f"⚡ {get_current_title(user['level'])}")
st.subheader(f"Niveau {user['level']} | Mode : {user['mode']}")
st.progress(min(user['xp'] / xp_target, 1.0))

tab_quests, tab_stats, tab_config = st.tabs(["⚔️ Quêtes", "📊 États & Titres", "⚙️ Config"])

# --- ONGLET 1 : QUÊTES ---
with tab_quests:
    quest_configs = {"Quotidiennes": {"base": 150, "max_w": 3}, "Hebdomadaires": {"base": 500, "max_w": 5}, "Mensuelles": {"base": 1500, "max_w": 7}, "Trimestrielles": {"base": 3000, "max_w": 9}, "Annuelles": {"base": 10000, "max_w": 11}}
    for q_type, q_info in quest_configs.items():
        tasks = user["task_lists"].get(q_type, [])
        if tasks:
            with st.expander(f"{q_type} ({len(tasks)})"):
                for t_name in tasks:
                    t_id = f"{q_type}_{t_name}"
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    is_done = t_id in user["completed_quests"]
                    c1.write(f"{'✅' if is_done else '🔳'} {t_name}")
                    if not is_done:
                        s = c2.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"], key=f"s_{t_id}")
                        w = c3.select_slider("Poids", options=list(range(1, q_info['max_w'] + 1)), key=f"w_{t_id}")
                        if c4.button("Valider", key=t_id):
                            gain = q_info['base'] * w
                            user['xp'] += gain
                            user['stats'][s] += w
                            user["completed_quests"].append(t_id)
                            # Log XP pour graphique OPM style
                            total_power = (user['level'] * 5000) + user['xp']
                            user["xp_history"].append({"point": len(user["xp_history"]), "power": total_power})
                            while user['xp'] >= get_xp_needed(user['level']):
                                user['xp'] -= get_xp_needed(user['level'])
                                user['level'] += 1
                            save_data(user); st.rerun()
                    else:
                        c4.button("Fait", key=t_id, disabled=True)

# --- ONGLET 2 : ÉTATS (STYLE OPM) ---
with tab_stats:
    col_graph, col_badges = st.columns([1.5, 1])
    
    with col_graph:
        st.subheader("📈 ÉVOLUTION DE PUISSANCE")
        if user["xp_history"]:
            df = pd.DataFrame(user["xp_history"])
            # Création du graphique style Garou vs Saitama
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['point'], y=df['power'],
                mode='lines+markers',
                line=dict(color='#00FFCC', width=4),
                fill='tozeroy',
                fillcolor='rgba(0, 255, 204, 0.1)',
                name="Ta Puissance"
            ))
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, title="Actions"),
                yaxis=dict(showgrid=True, gridcolor='#333', title="Niveau de Menace"),
                font=dict(color="#00FFCC")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Données en attente...")

        st.subheader("📊 Caractéristiques")
        c_s1, c_s2, c_s3, c_s4 = st.columns(4)
        c_s1.metric("Physique", user['stats']['Physique'])
        c_s2.metric("Connaissances", user['stats']['Connaissances'])
        c_s3.metric("Autonomie", user['stats']['Autonomie'])
        c_s4.metric("Mental", user['stats']['Mental'])

    with col_badges:
        st.subheader("🏆 Arbre des Titres")
        cols = st.columns(2)
        for i, (lvl_req, title) in enumerate(TITLES_MAP.items()):
            with cols[i % 2]:
                unlocked = user['level'] >= lvl_req
                st.markdown(f"""
                    <div style="background:{'#1E1E1E' if unlocked else '#0A0A0A'}; border:2px solid {'#00FFCC' if unlocked else '#333'}; padding:10px; border-radius:10px; text-align:center; margin-bottom:10px;">
                        <span style="color:{'#00FFCC' if unlocked else '#444'}; font-size:0.7em;">Niveau {lvl_req}</span><br>
                        <b style="color:{'white' if unlocked else '#444'};">{title if unlocked else '???'}</b>
                    </div>
                """, unsafe_allow_html=True)

# --- ONGLET 3 : CONFIG (CORRIGÉ) ---
with tab_config:
    st.subheader("⚙️ Configuration")
    user["mode"] = st.radio("Mode :", ["Nomade", "Séide", "Exalté"], index=["Nomade", "Séide", "Exalté"].index(user["mode"]))
    if st.button("Sauvegarder Mode"):
        save_data(user); st.success("Mode mis à jour.")
    
    st.divider()
    cat = st.selectbox("Catégorie de quêtes :", list(quest_configs.keys()))
    
    # Ajout
    new_t = st.text_input(f"Nouvel objectif {cat} :")
    if st.button("Ajouter"):
        if new_t:
            user["task_lists"][cat].append(new_t)
            save_data(user); st.rerun()
    
    st.divider()
    # LISTE DE SUPPRESSION (Rétablie)
    st.write(f"Liste actuelle ({cat}) :")
    for t in user["task_lists"].get(cat, []):
        col_name, col_btn = st.columns([4, 1])
        col_name.write(f"• {t}")
        if col_btn.button("❌", key=f"del_{cat}_{t}"):
            user["task_lists"][cat].remove(t)
            save_data(user); st.rerun()

with st.sidebar:
    if st.button("🔄 Nouvelle Journée"):
        user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith("Quotidiennes")]
        save_data(user); st.rerun()
