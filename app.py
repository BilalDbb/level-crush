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

# --- 2. LOGIQUE XP (TA FORMULE) ---
def get_xp_required(lvl):
    next_lvl = lvl + 1
    if lvl < 5: return int(200 * (next_lvl**1.2))
    elif 5 <= lvl < 100: return int(25 * (next_lvl**1.2))
    else: return int(int(25 * (100**1.2)) * 10)

def get_total_cumulated_xp(lvl, current_xp):
    total = 0
    for l in range(1, lvl):
        total += get_xp_required(l)
    return total + current_xp

def generate_simulation():
    """Génère un historique propre depuis Février 2025"""
    history = []
    curr = datetime(2025, 2, 1)
    t_lvl, t_xp = 1, 0
    while curr <= datetime.now():
        chance = random.random()
        status = "rouge" if chance < 0.15 else ("orange" if chance < 0.35 else "fait")
        gain = random.randint(100, 500) if status != "rouge" else 0
        t_xp += gain
        req = get_xp_required(t_lvl)
        lvl_up = False
        if t_xp >= req and t_lvl < 100:
            t_xp -= req; t_lvl += 1; lvl_up = True
        history.append({
            "date": curr.strftime("%Y-%m-%d"),
            "xp_total": get_total_cumulated_xp(t_lvl, t_xp),
            "status": status,
            "level_up": lvl_up
        })
        curr += timedelta(days=2)
    return history

# --- 3. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 

def load_data():
    try:
        res = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if res.data:
            d = res.data[0]['data']
            if isinstance(d, str): d = json.loads(d)
            # Init des champs manquants
            f = {"level": 1, "xp": 0, "mode": "Séide", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, "xp_history": []}
            for k, v in f.items():
                if k not in d: d[k] = v
            if not d["xp_history"]: d["xp_history"] = generate_simulation()
            return d
    except: pass
    return {"level": 1, "xp": 0, "mode": "Séide", "xp_history": generate_simulation(), "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}}

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
            u['xp'] -= req; u['level'] += 1; st.toast("🌟 LEVEL UP !")
        else: break
    if u['mode'] == "Exalté":
        while u['xp'] < 0 and u['level'] > 1:
            u['level'] -= 1; u['xp'] += get_xp_required(u['level']); st.toast("📉 LEVEL DOWN...")
    if u['xp'] < 0: u['xp'] = 0

# --- 4. INTERFACE ---
TITLES = {1: "Rang E", 3: "Néophyte", 6: "Aspirant", 10: "Soldat de Plomb", 14: "Gardien de Fer", 19: "Traqueur Silencieux", 24: "Vanguard", 30: "Chevalier d'Acier", 36: "Briseur de Chaînes", 43: "Architecte du Destin", 50: "Légat du Système", 58: "Commandeur", 66: "Seigneur de Guerre", 75: "Entité Transcendante", 84: "Demi-Dieu", 93: "Souverain", 100: "LEVEL CRUSHER"}

st.set_page_config(page_title="LEVEL CRUSH", layout="wide")
st.markdown(f"<h1 style='text-align:center; color:#00FFCC;'>⚡ NIV.{u['level']} | {TITLES.get(max([l for l in TITLES if l <= u['level']]), 'Inconnu')}</h1>", unsafe_allow_html=True)

tabs = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🏆 Titres", "🧩 Système", "⚙️ Configuration"])

# --- TAB 1 : QUÊTES ---
with tabs[0]:
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
                    done = task in u["completed_quests"]
                    c = st.columns([2, 1, 0.5, 0.5] if u['mode'] == "Exalté" else [2, 1, 1])
                    c[0].write(f"{'✅' if done else '🔳'} {task}")
                    if not done:
                        diff = c[1].select_slider("Diff", options=list(range(1, m_d+1)), key=f"s_{idx}", label_visibility="collapsed")
                        if c[2].button("✔️", key=f"v_{idx}"):
                            process_xp_change(100 * diff)
                            u["completed_quests"].append(task)
                            u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp_total": get_total_cumulated_xp(u['level'], u['xp']), "status":"fait", "level_up": False})
                            save_data(u); st.rerun()
                        if u['mode'] == "Exalté" and len(c) > 3:
                            if c[3].button("❌", key=f"x_{idx}"):
                                process_xp_change(-(100 * diff))
                                u["xp_history"].append({"date": datetime.now().strftime("%Y-%m-%d"), "xp_total": get_total_cumulated_xp(u['level'], u['xp']), "status":"rouge", "level_up": False})
                                save_data(u); st.rerun()
                    idx += 1

# --- TAB 2 : STATISTIQUES ---
with tabs[1]:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("📈 Progression")
        df = pd.DataFrame(u["xp_history"])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            # FIX KEYERROR : On cherche xp_total, sinon xp, sinon on ignore
            y_col = 'xp_total' if 'xp_total' in df.columns else ('xp' if 'xp' in df.columns else None)
            if y_col:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['date'], y=df[y_col], mode='lines', line=dict(color='#00FFCC', width=2), name="XP Cumulée"))
                for s, color, lab in [('rouge','red','Échec'), ('orange','orange','Partiel'), ('fait','#00FFCC','Succès')]:
                    sub = df[df['status']==s]
                    if not sub.empty: fig.add_trace(go.Scatter(x=sub['date'], y=sub[y_col], mode='markers', marker=dict(color=color, size=5), name=lab))
                fig.update_layout(template="plotly_dark", height=450, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🕸️ Profil de Puissance")
        fig_r = go.Figure(data=go.Scatterpolar(r=list(u['stats'].values()), theta=list(u['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(u['stats'].values())+15])), template="plotly_dark", height=450)
        st.plotly_chart(fig_r, use_container_width=True)

# --- TAB 3 : TITRES ---
with tabs[2]:
    st.subheader("🎖️ Arbre des Titres")
    cols = st.columns(4)
    for i, (l_req, title) in enumerate(TITLES.items()):
        unlocked = u['level'] >= l_req
        with cols[i % 4]:
            st.markdown(f"<div style='background:{'#1E1E1E' if unlocked else '#0A0A0A'}; border:2px solid {'#00FFCC' if unlocked else '#333'}; padding:15px; border-radius:10px; text-align:center; margin-bottom:15px;'><span style='color:{'#00FFCC' if unlocked else '#444'}; font-size:0.8em;'>Niveau {l_req}</span><br><b style='color:{'white' if unlocked else '#444'};'>{title if unlocked else '???'}</b></div>", unsafe_allow_html=True)

# --- TAB 4 : SYSTÈME ---
with tabs[3]:
    st.subheader("🧩 Architecture")
    st.write("**Modes :** Séide (Sécurité) | Exalté (Danger / Level Down).")
    st.write("**Courbe XP :** $Coef \\times Niveau^{1.2}$ (Coef 200 au début, 25 ensuite).")

# --- TAB 5 : CONFIGURATION ---
with tabs[4]:
    new_m = st.radio("Difficulté", ["Séide", "Exalté"], index=["Séide", "Exalté"].index(u["mode"]), help="Séide: Sécurisé | Exalté: Hardcore.")
    if new_m != u["mode"]: u["mode"] = new_m; save_data(u); st.rerun()
    st.divider()
    cp, ct, cb = st.columns([1, 2, 1])
    p_sel = cp.selectbox("Période", list(u["task_lists"].keys()))
    t_add = ct.text_input("Tâche")
    if cb.button("Ajouter"):
        all_t = [t for sub in u["task_lists"].values() for t in sub]
        if t_add not in all_t and t_add: u["task_lists"][p_sel].append(t_add); save_data(u); st.rerun()
    for p, tasks in u["task_lists"].items():
        if tasks:
            st.write(f"**{p}**")
            for i, t in enumerate(tasks):
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {t}")
                if cx2.button("❌", key=f"del_{p}_{i}"):
                    u["task_lists"][p].remove(t); save_data(u); st.rerun()

# --- SIDEBAR (RESETS & TEMPS) ---
with st.sidebar:
    st.header("⏳ Temps")
    if st.button("⏭️ SAUTER UN JOUR", use_container_width=True):
        if u['mode'] == "Exalté":
            d_count = len(u["task_lists"].get("Quotidiennes", []))
            process_xp_change(-(d_count * 100) if d_count > 0 else -500)
        u["completed_quests"] = [q for q in u["completed_quests"] if q not in u["task_lists"].get("Quotidiennes", [])]
        save_data(u); st.rerun()
    st.header("🔄 Resets")
    for p in u["task_lists"].keys():
        if st.button(f"Reset {p}", key=f"rs_{p}"):
            u["completed_quests"] = [q for q in u["completed_quests"] if q not in u["task_lists"].get(p, [])]
            save_data(u); st.rerun()
