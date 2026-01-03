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
            # Init sécurité
            if "level" not in data: data["level"] = 1
            if "xp" not in data: data["xp"] = 0
            if "mode" not in data: data["mode"] = "Nomade"
            if "task_diffs" not in data: data["task_diffs"] = {} # Stocke la difficulté choisie
            if "stats" not in data: data["stats"] = {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Nomade", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": []}, "task_diffs": {}}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

user = load_data() if 'user_data' not in st.session_state else st.session_state.user_data

# --- 3. LOGIQUE TITRES ---
TITLES_MAP = {3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 14: "Gardien de Fer", 19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 58: "Commandeur", 66: "Seigneur de Guerre", 75: "Entité Transcendante", 84: "Demi-Dieu", 93: "Souverain de l'Abysse", 100: "LEVEL CRUSHER"}

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡", layout="wide")

st.markdown(f"<h1 style='text-align: center; color: #00FFCC;'>⚡ NIV.{user['level']} | {TITLES_MAP.get(user['level'], 'Souverain')}</h1>", unsafe_allow_html=True)

tab_quests, tab_stats, tab_config = st.tabs(["⚔️ Quêtes", "🏆 Titres & Statistiques", "⚙️ Configuration"])

# --- ONGLET 1 : QUÊTES ---
with tab_quests:
    st.info("⚖️ **Équilibre Miroir** : L'XP perdue en cas d'échec est égale à l'XP que vous auriez gagnée (100 XP x Difficulté).")
    
    for q_type, max_diff in {"Quotidiennes": 3, "Hebdomadaires": 5, "Mensuelles": 7, "Trimestrielles": 9, "Annuelles": 11}.items():
        tasks = user["task_lists"].get(q_type, [])
        if tasks:
            with st.expander(f"{q_type} ({len(tasks)})"):
                for t in tasks:
                    t_id = f"{q_type}_{t}"
                    is_done = t_id in user["completed_quests"]
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"{'✅' if is_done else '🔳'} {t}")
                    
                    # On récupère la dernière difficulté connue ou on met par défaut
                    current_d = user["task_diffs"].get(t_id, 1)
                    
                    if not is_done:
                        new_d = c2.select_slider("Difficulté", options=list(range(1, max_diff+1)), value=current_d, key=f"sl_{t_id}", label_visibility="collapsed")
                        user["task_diffs"][t_id] = new_d # Mémorisation pour le calcul de perte
                        if c3.button("Valider", key=f"btn_{t_id}"):
                            user['xp'] += (100 * new_d)
                            user["completed_quests"].append(t_id)
                            save_data(user); st.rerun()
                    else:
                        c3.button("Fait", key=f"done_{t_id}", disabled=True)

# --- ONGLET 2 : STATS & TITRES ---
with tab_stats:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🏆 Arbre des Titres")
        cols = st.columns(4)
        for i, (lvl_req, title) in enumerate(TITLES_MAP.items()):
            unlocked = user['level'] >= lvl_req
            with cols[i % 4]:
                st.markdown(f"""
                <div style="background:{'#1E1E1E' if unlocked else '#0A0A0A'}; border:2px solid {'#00FFCC' if unlocked else '#333'}; padding:10px; border-radius:10px; text-align:center; margin-bottom:10px;">
                    <span style="color:{'#00FFCC' if unlocked else '#444'}; font-size:0.7em;">Niv. {lvl_req}</span><br>
                    <b style="color:{'white' if unlocked else '#444'}; font-size:0.8em;">{title if unlocked else '???'}</b>
                </div>
                """, unsafe_allow_html=True)
    with c2:
        st.subheader("🕸️ Profil de Puissance")
        labels = list(user['stats'].keys())
        values = list(user['stats'].values())
        fig_radar = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself', line_color='#00FFCC'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(values)+10])), template="plotly_dark", margin=dict(l=80, r=80, t=40, b=40))
        st.plotly_chart(fig_radar, use_container_width=True)

# --- ONGLET 3 : CONFIGURATION ---
with tab_config:
    help_modes = {"Nomade": "Aucune pénalité.", "Séide": "Perte XP miroir. Pas de de-level.", "Exalté": "Perte XP miroir + De-level possible."}
    user["mode"] = st.radio("Mode de jeu", ["Nomade", "Séide", "Exalté"], help=help_modes[user.get("mode", "Nomade")])
    if st.button("Sauvegarder Configuration"): save_data(user); st.success("Système mis à jour.")
    
    st.divider()
    for p, tasks in user["task_lists"].items():
        if tasks:
            st.write(f"**{p}**")
            for t in tasks:
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {t}")
                if cx2.button("❌", key=f"del_{p}_{t}"):
                    user["task_lists"][p].remove(t); save_data(user); st.rerun()

with st.sidebar:
    st.header("⚡ Actions Système")
    for p in ["Quotidiennes", "Hebdomadaires", "Mensuelles"]:
        if st.button(f"🔄 Reset {p}"):
            if user["mode"] != "Nomade":
                tasks = user["task_lists"].get(p, [])
                penalty = 0
                for t in tasks:
                    t_id = f"{p}_{t}"
                    if t_id not in user["completed_quests"]:
                        diff = user["task_diffs"].get(t_id, 1)
                        penalty += (100 * diff)
                
                if penalty > 0:
                    user["xp"] -= penalty
                    st.error(f"Pénalité Miroir : -{penalty} XP")
                    if user["mode"] == "Exalté" and user["xp"] < 0:
                        if user["level"] > 1: user
