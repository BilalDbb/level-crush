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

# --- 2. LOGIQUE DE PROGRESSION (TA FORMULE) ---
def get_xp_required(lvl):
    """Calcul selon tes paliers : Coef 200 (L<5) | Coef 25 (L<100) | x10 (L=100)"""
    next_lvl = lvl + 1
    if lvl < 5:
        return int(200 * (next_lvl**1.2))
    elif 5 <= lvl < 100:
        return int(25 * (next_lvl**1.2))
    else: # Niveau 100
        return int(int(25 * (100**1.2)) * 10)

def generate_plausible_history():
    """Simule une progression réaliste basée sur ta courbe depuis Juin 2025"""
    history = []
    curr_date = datetime(2025, 6, 1)
    temp_lvl = 1
    temp_xp = 0
    total_xp_cumul = 0
    
    while curr_date <= datetime.now():
        chance = random.random()
        status = "rouge" if chance < 0.2 else ("orange" if chance < 0.4 else "fait")
        gain = random.randint(100, 400) if status != "rouge" else 0
        
        temp_xp += gain
        total_xp_cumul += gain
        req = get_xp_required(temp_lvl)
        
        level_up_occurred = False
        if temp_xp >= req and temp_lvl < 100:
            temp_xp -= req
            temp_lvl += 1
            level_up_occurred = True
            
        history.append({
            "date": curr_date.strftime("%Y-%m-%d"),
            "xp": total_xp_cumul,
            "status": status,
            "level_up": level_up_occurred
        })
        curr_date += timedelta(days=2)
    return history

# --- 3. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    try:
        response = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if response.data:
            data = response.data[0]['data']
            if isinstance(data, str): data = json.loads(data)
            fields = {
                "level": 1, "xp": 0, "mode": "Séide", 
                "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10},
                "completed_quests": [], "task_diffs": {}, "xp_history": [],
                "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}
            }
            for k, v in fields.items():
                if k not in data: data[k] = v
            if not data["xp_history"]: data["xp_history"] = generate_plausible_history()
            return data
    except: pass
    return {"level": 1, "xp": 0, "mode": "Séide", "xp_history": generate_plausible_history(), "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()
u = st.session_state.user_data

def process_xp_change(amount):
    u['xp'] += amount
    while True:
        req = get_xp_required(u['level'])
        if u['xp'] >= req and u['level'] < 100:
            u['xp'] -= req
            u['level'] += 1
            st.toast("🌟 LEVEL UP !")
        else: break
    if u['mode'] == "Exalté":
        while u['xp'] < 0 and u['level'] > 1:
            u['level'] -= 1
            u['xp'] += get_xp_required(u['level'])
            st.toast("⚠️ LEVEL DOWN...", icon="📉")
    if u['xp'] < 0: u['xp'] = 0

# --- 4. CONFIGURATION TITRES ---
TITLES_MAP = {
    1: "Soldat de Rang E", 3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 
    14: "Gardien de Fer", 19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 
    36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 
    58: "Commandeur", 66: "Seigneur de Guerre", 75: "Entité Transcendante", 
    84: "Demi-Dieu", 93: "Souverain de l'Abysse", 100: "LEVEL CRUSHER"
}

def get_current_title(lvl):
    unlocked = [t for l, t in TITLES_MAP.items() if l <= lvl]
    return unlocked[-1] if unlocked else "Inconnu"

# --- 5. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", layout="wide")
st.markdown(f"<h1 style='text-align:center; color:#00FFCC;'>⚡ NIV.{u['level']} | {get_current_title(u['level'])}</h1>", unsafe_allow_html=True)

t_q, t_s, t_t, t_sys, t_c = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "🧩 Système", "⚙️ Configuration"])

# --- TAB QUÊTES ---
with t_q:
    req = get_xp_required(u['level'])
    st.subheader(f"🚀 Progression : {u['xp']} / {req} XP")
    st.progress(min(max(u['xp']/req, 0.0), 1.0))
    st.divider()
    
    idx = 0
    for q_p, m_d in {"Quotidiennes":3, "Hebdomadaires":5, "Mensuelles":7, "Trimestrielles":9, "Annuelles":11}.items():
        tasks = u["task_lists"].get(q_p, [])
        if tasks:
            with st.expander(f"{q_p} ({len(tasks)})", expanded=True):
                for task in tasks:
                    t_id = f"{q_p}_{task}"
                    done = t_id in u["completed_quests"]
                    col_spec = [2, 1, 0.5, 0.5] if u['mode'] == "Exalté" else [2, 1, 1]
                    cols = st.columns(col_spec)
                    cols[0].write(f"{'✅' if done else '🔳'} {task}")
                    if not done:
                        diff = cols[1].select_slider("Diff", options=list(range(1, m_d+1)), key=f"s_{idx}", label_visibility="collapsed")
                        if cols[2].button("✔️", key=f"v_{idx}"):
                            process_xp_change(100 * diff)
                            u["completed_quests"].append(t_id)
                            u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": u['xp'], "status":"fait"})
                            save_data(u); st.rerun()
                        if u['mode'] == "Exalté":
                            if cols[3].button("❌", key=f"x_{idx}"):
                                process_xp_change(-(100 * diff))
                                u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp": u['xp'], "status":"rouge"})
                                save_data(u); st.rerun()
                    idx += 1

# --- TAB STATISTIQUES ---
with t_s:
    c_xy, c_rd = st.columns([1.2, 1])
    with c_xy:
        st.subheader("📈 Progression")
        df = pd.DataFrame(u["xp_history"])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp'], mode='lines', line=dict(color='#00FFCC', width=2), name="Courbe XP"))
            for s, color, lab in [('rouge','red', 'Échec'), ('fait','#00FFCC', 'Succès'), ('orange', 'orange', 'Partiel')]:
                sub = df[df['status']==s]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['date'], y=sub['xp'], mode='markers', marker=dict(color=color, size=6), name=lab))
            fig.update_layout(template="plotly_dark", height=400, showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    with c_rd:
        st.subheader("🕸️ Profil de Puissance")
        fig_r = go.Figure(data=go.Scatterpolar(r=list(u['stats'].values()), theta=list(u['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(u['stats'].values())+15])), template="plotly_dark", height=400)
        st.plotly_chart(fig_r, use_container_width=True)

# --- TAB TITRES ---
with t_t:
    st.subheader("🎖️ Arbre des Titres")
    cols = st.columns(4)
    for i, (l_req, title) in enumerate(TITLES_MAP.items()):
        unlocked = u['level'] >= l_req
        with cols[i % 4]:
            st.markdown(f"<div style='background:{'#1E1E1E' if unlocked else '#0A0A0A'}; border:2px solid {'#00FFCC' if unlocked else '#333'}; padding:15px; border-radius:10px; text-align:center; margin-bottom:15px;'><span style='color:{'#00FFCC' if unlocked else '#444'}; font-size:0.8em;'>Niveau {l_req}</span><br><b style='color:{'white' if unlocked else '#444'};'>{title if unlocked else '???'}</b></div>", unsafe_allow_html=True)

# --- TAB SYSTÈME ---
with t_sys:
    st.subheader("🧩 Architecture")
    st.markdown("""
    **⚖️ Fonctionnement de la Difficulté**
    Le curseur de difficulté multiplie vos gains d'XP et de Statistiques. 
    
    **🎮 Modes de Jeu**
    - **Séide** : Aucune pénalité si tâches non accomplies.
    - **Exalté** : Perte d'XP et de niveau possible.
    
    **📈 Évolution de Capacité**
    - Tous les 10 niveaux : Déblocage d'un nouvel emplacement de tâche.
    """)

# --- TAB CONFIGURATION ---
with t_c:
    h_msg = "Séide : Aucune pénalité si tâches non accomplies. | Exalté : Perte de niveau et d'XP possible."
    new_m = st.radio("Difficulté", ["Séide", "Exalté"], index=["Séide", "Exalté"].index(u["mode"]), help=h_msg)
    if new_m != u["mode"]:
        u["mode"] = new_m
        save_data(u); st.rerun()
    st.divider()
    cp, ct, cb = st.columns([1, 2, 1])
    sel_p = cp.selectbox("Période", list(u["task_lists"].keys()))
    name_t = ct.text_input("Tâche")
    if cb.button("Ajouter"):
        if name_t: u["task_lists"][sel_p].append(name_t); save_data(u); st.rerun()
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
    st.header("⏳ Temps")
    if st.button("⏭️ SAUTER UN JOUR", use_container_width=True):
        if u['mode'] == "Exalté":
            d_count = len(u["task_lists"].get("Quotidiennes", []))
            process_xp_change(-(d_count * 100) if d_count > 0 else -500)
        u["completed_quests"] = [q for q in u["completed_quests"] if not q.startswith("Quotidiennes")]
        save_data(u); st.rerun()
    st.header("🔄 Resets")
    for p in u["task_lists"].keys():
        if st.button(f"Reset {p}", key=f"rs_{p}"):
            u["completed_quests"] = [q for q in u["completed_quests"] if not q.startswith(p)]
            save_data(u); st.rerun()
