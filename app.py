import streamlit as st
import json
import pandas as pd
import plotly.express as px
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
            if "task_lists" not in data: data["task_lists"] = {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}
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

# --- 3. LOGIQUE TITRES & XP ---
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
            with st.expander(f"{q_type}"):
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
                            # Historique XP pour graphique
                            user["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "xp_total": user['xp'] + (user['level']*1000)}) # On ajoute un offset pour la courbe
                            while user['xp'] >= get_xp_needed(user['level']):
                                user['xp'] -= get_xp_needed(user['level'])
                                user['level'] += 1
                            save_data(user); st.rerun()
                    else:
                        c4.button("Fait", key=t_id, disabled=True)

# --- ONGLET 2 : ÉTATS & TITRES ---
with tab_stats:
    c_left, c_right = st.columns([1, 1])
    
    with c_left:
        st.subheader("📈 Évolution de l'XP")
        if user["xp_history"]:
            df = pd.DataFrame(user["xp_history"])
            fig = px.line(df, x="date", y="xp_total", title="Courbe de Progression", markers=True)
            fig.update_traces(line_color='#00FFCC')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Valide ta première quête pour voir la courbe.")

        st.subheader("📊 Caractéristiques")
        st.write(f"💪 **Physique** : {user['stats']['Physique']}")
        st.write(f"🧠 **Connaissances** : {user['stats']['Connaissances']}")
        st.write(f"🛠️ **Autonomie** : {user['stats']['Autonomie']}")
        st.write(f"🧘 **Mental** : {user['stats']['Mental']}")

    with c_right:
        st.subheader("🏆 Arbre des Titres")
        # Affichage en grille/badges
        cols = st.columns(3)
        for i, (lvl_req, title) in enumerate(TITLES_MAP.items()):
            with cols[i % 3]:
                unlocked = user['level'] >= lvl_req
                color = "green" if unlocked else "gray"
                st.markdown(f"""
                <div style="border: 2px solid {color}; border-radius: 10px; padding: 10px; text-align: center; margin-bottom: 10px; background-color: {'#1E1E1E' if unlocked else '#0E0E0E'}">
                    <span style="color: {color}; font-size: 0.8em;">Niv. {lvl_req}</span><br>
                    <b style="color: {'white' if unlocked else '#555'}">{title if unlocked else '???'}</b>
                </div>
                """, unsafe_allow_html=True)

# --- ONGLET 3 : CONFIG ---
with tab_config:
    st.subheader("🎮 Paramètres du Système")
    user["mode"] = st.radio("Mode de Jeu :", ["Nomade", "Séide", "Exalté"], index=["Nomade", "Séide", "Exalté"].index(user["mode"]))
    if st.button("Enregistrer le Mode"):
        save_data(user); st.success(f"Mode {user['mode']} activé.")
    
    st.divider()
    st.subheader("⚙️ Gestionnaire de Quêtes")
    cat = st.selectbox("Catégorie :", list(quest_configs.keys()))
    new_t = st.text_input(f"Nouvel objectif {cat} :")
    if st.button("Ajouter"):
        if new_t and new_t not in user["task_lists"][cat]:
            user["task_lists"][cat].append(new_t); save_data(user); st.rerun()

with st.sidebar:
    if st.button("🔄 Nouvelle Journée"):
        # Logique de sanction selon le mode
        not_done = 0 # On pourrait compter les quêtes quotidiennes non faites ici
        user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith("Quotidiennes")]
        save_data(user); st.rerun()
