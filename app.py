import streamlit as st
import json
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONNEXION SUPABASE ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur de connexion Cloud : {e}")
    st.stop()

# --- 2. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data and len(response.data) > 0:
            raw_data = response.data[0]['data']
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            if "task_lists" not in data:
                data["task_lists"] = {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}
            if "stats" not in data: data["stats"] = {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}
            if "completed_quests" not in data: data["completed_quests"] = []
            return data
    except: pass
    return {"level": 1, "xp": 0, "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

# --- 3. LOGIQUE DES TITRES & CLASSES ---
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

def get_specialization(stats):
    if all(v == 0 for v in stats.values()): return "Civil"
    max_stat = max(stats, key=stats.get)
    max_val = stats[max_stat]
    
    # Vérifier l'équilibre (si la différence est minime entre toutes les stats)
    vals = list(stats.values())
    if max(vals) - min(vals) < 5 and sum(vals) > 20:
        return "Polytechnicien"
        
    specialities = {
        "Physique": "Guerrier",
        "Connaissances": "Érudit",
        "Autonomie": "Artisan",
        "Mental": "Ascète"
    }
    return specialities.get(max_stat, "Polyvalent")

# --- 4. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")

def get_xp_needed(lvl):
    exponent = 1.25 
    coeff = 200 if lvl < 5 else 25 
    return int(coeff * (lvl**exponent))

xp_target = get_xp_needed(user['level'])
current_spec = get_specialization(user['stats'])

# HEADER ÉPIQUE
st.title(f"⚡ {get_current_title(user['level'])}")
st.subheader(f"Classe : {current_spec} | Niveau {user['level']}")
st.progress(min(user['xp'] / xp_target, 1.0))
st.caption(f"XP : {user['xp']} / {xp_target}")

tab_quests, tab_stats, tab_config = st.tabs(["⚔️ Quêtes", "📊 État", "⚙️ Config"])

# --- ONGLET QUÊTES ---
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
                            user['xp'] += (q_info['base'] * w)
                            user['stats'][s] += w
                            user["completed_quests"].append(t_id)
                            while user['xp'] >= get_xp_needed(user['level']):
                                user['xp'] -= get_xp_needed(user['level'])
                                user['level'] += 1
                            save_data(user); st.rerun()
                    else:
                        c4.button("Fait", key=t_id, disabled=True)

# --- ONGLET STATS (MIS À JOUR) ---
with tab_stats:
    st.subheader("📊 Caractéristiques")
    sc1, sc2 = st.columns(2)
    sc1.metric("💪 Physique", user['stats']['Physique'])
    sc1.metric("🧠 Connaissances", user['stats']['Connaissances'])
    sc2.metric("🛠️ Autonomie", user['stats']['Autonomie'])
    sc2.metric("🧘 Mental", user['stats']['Mental'])
    
    st.divider()
    st.subheader("🏆 Arbre des Titres")
    for lvl_req, title in TITLES_MAP.items():
        col_t1, col_t2 = st.columns([1, 4])
        if user['level'] >= lvl_req:
            col_t1.success(f"Niv. {lvl_req}")
            col_t2.write(f"**{title}**")
        else:
            col_t1.info(f"Niv. {lvl_req}")
            col_t2.write("*[VERROUILLÉ]*")

# --- ONGLET CONFIG ---
with tab_config:
    cat = st.selectbox("Catégorie :", list(quest_configs.keys()))
    new_t = st.text_input(f"Nouvel objectif {cat} :")
    if st.button("Ajouter"):
        if new_t and new_t not in user["task_lists"][cat]:
            user["task_lists"][cat].append(new_t); save_data(user); st.rerun()
    st.divider()
    for t in user["task_lists"][cat]:
        c_t, c_d = st.columns([4, 1])
        c_t.write(f"- {t}")
        if c_d.button("❌", key=f"del_{cat}_{t}"):
            user["task_lists"][cat].remove(t); save_data(user); st.rerun()

with st.sidebar:
    if st.button("🔄 Reset Quotidiennes"):
        user["completed_quests"] = [q for q in user["completed_quests"] if not q.startswith("Quotidiennes")]
        save_data(user); st.rerun()
