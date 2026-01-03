import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. CONNEXION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur Cloud : {e}")
    st.stop()

# --- 2. LOGIQUE SYSTÈME ---
def get_xp_required(lvl):
    next_lvl = lvl + 1
    if lvl < 5: return int(200 * (next_lvl**1.2))
    elif 5 <= lvl < 100: return int(25 * (next_lvl**1.2))
    else: return int(int(25 * (100**1.2)) * 10)

def get_total_cumulated_xp(lvl, current_xp):
    total = 0
    for l in range(1, lvl): total += get_xp_required(l)
    return total + current_xp

def get_capacity_for_period(lvl, period):
    if period == "Quotidiennes": return 4 + (lvl // 20)
    return 1

# --- 3. CONFIGURATION DES TITRES & BADGES ---
TITLES_DATA = [
    (1, "Starter", "#7F8C8D"), (3, "Néophyte", "#95A5A6"), (6, "Aspirant", "#BDC3C7"),
    (10, "Soldat de Plomb", "#D35400"), (14, "Gardien de Fer", "#95A5A6"), (19, "Traqueur Silencieux", "#2C3E50"),
    (24, "Vanguard", "#2980B9"), (30, "Chevalier d'Acier", "#34495E"), (36, "Briseur de Chaînes", "#E67E22"),
    (43, "Architecte du Destin", "#8E44AD"), (50, "Légat du Système", "#16A085"), (58, "Commandeur", "#27AE60"),
    (66, "Seigneur de Guerre", "#C0392B"), (75, "Entité Transcendante", "#F1C40F"), (84, "Demi-Dieu", "#F39C12"),
    (93, "Souverain", "#E74C3C"), (100, "LEVEL CRUSHER", "#00FFCC")
]

def get_current_title_info(lvl):
    current = TITLES_DATA[0]
    for l_req, name, color in TITLES_DATA:
        if lvl >= l_req: current = (l_req, name, color)
    return current

# --- 4. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 

def get_default_data():
    return {
        "level": 1, "xp": 0, "mode": "Séide", 
        "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10},
        "completed_quests": [], 
        "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []},
        "task_diffs": {}, "xp_history": [], "internal_date": "2026-01-03"
    }

def load_data():
    try:
        res = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if res.data:
            d = res.data[0]['data']
            if isinstance(d, str): d = json.loads(d)
            f = get_default_data()
            for k, v in f.items():
                if k not in d: d[k] = v
            return d
    except: pass
    return get_default_data()

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()
u = st.session_state.user_data

def process_xp_change(amount, status="fait"):
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
    u["xp_history"].append({"date": u["internal_date"], "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']), "status": status})

# --- 5. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", layout="wide")

# HEADER AVEC BADGE DYNAMIQUE
_, title_name, title_color = get_current_title_info(u['level'])
st.markdown(f"""
    <div style="text-align:center; padding:10px;">
        <span style="color:white; font-size:1.1em; vertical-align:middle;">NIV.{u['level']}</span>
        <div style="display:inline-block; margin-left:12px; padding:4px 18px; border:2px solid {title_color}; 
                    border-radius:20px; box-shadow: 0 0 12px {title_color};">
            <b style="color:{title_color}; font-size:1.3em; text-transform:uppercase; letter-spacing:1px;">{title_name}</b>
        </div>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🧩 Système", "⚙️ Configuration"])

# --- TAB 1 : QUÊTES & REGISTRE ---
with tabs[0]:
    req = get_xp_required(u['level'])
    st.progress(min(max(u['xp']/req, 0.0), 1.0))
    st.write(f"XP : **{u['xp']} / {req}**")
    
    with st.expander("📜 Registre des Rangs", expanded=False):
        # Timeline Horizontale avec injection HTML propre
        timeline_items = ""
        for l_req, t_name, t_color in TITLES_DATA:
            is_unlocked = u['level'] >= l_req
            is_current = get_current_title_info(u['level'])[0] == l_req
            disp_name = t_name if is_unlocked else "???"
            dot_color = t_color if is_unlocked else "#333"
            opacity = "1" if is_unlocked else "0.4"
            pulse_class = "pulse-active" if is_current else ""
            border_style = f"border: 2px solid {'white' if is_current else 'transparent'};"
            
            timeline_items += f"""
                <div style="min-width: 90px; text-align: center; opacity: {opacity}; margin-right: 15px;">
                    <div class="dot {pulse_class}" style="width: 14px; height: 14px; background: {dot_color}; border-radius: 50%; margin: 0 auto; {border_style}"></div>
                    <p style="font-size: 0.65em; color: {dot_color}; margin-top: 8px; font-weight: bold; white-space: nowrap;">{disp_name}</p>
                    <p style="font-size: 0.55em; color: #666; margin-top: -5px;">Niv.{l_req}</p>
                </div>
            """
        
        st.markdown(f"""
            <style>
            @keyframes pulse-anim {{
                0% {{ box-shadow: 0 0 0 0 {title_color}77; }}
                70% {{ box-shadow: 0 0 0 8px {title_color}00; }}
                100% {{ box-shadow: 0 0 0 0 {title_color}00; }}
            }}
            .pulse-active {{ animation: pulse-anim 2s infinite; }}
            .scroll-container {{
                display: flex; 
                overflow-x: auto; 
                padding: 15px 5px; 
                scroll-behavior: smooth;
                -webkit-overflow-scrolling: touch;
            }}
            .scroll-container::-webkit-scrollbar {{ height: 4px; }}
            .scroll-container::-webkit-scrollbar-thumb {{ background: #333; border-radius: 10px; }}
            </style>
            <div class="scroll-container">
                {timeline_items}
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # LISTE DES QUÊTES
    idx = 0
    for q_p in ["Quotidiennes", "Hebdomadaires", "Mensuelles", "Trimestrielles", "Annuelles"]:
        tasks = u["task_lists"].get(q_p, [])
        if tasks:
            cap = get_capacity_for_period(u['level'], q_p)
            with st.expander(f"{q_p} ({len(tasks)}/{cap})", expanded=True):
                for task in tasks:
                    done = task in u["completed_quests"]
                    c = st.columns([2, 1, 0.5, 0.5] if u['mode'] == "Exalté" else [2, 1, 1])
                    c[0].write(f"{'✅' if done else '🔳'} {task}")
                    if not done:
                        m_d = {"Quotidiennes":3, "Hebdomadaires":5, "Mensuelles":7, "Trimestrielles":9, "Annuelles":11}[q_p]
                        val_diff = u["task_diffs"].get(task, 1)
                        diff = c[1].select_slider("Poids", options=list(range(1, m_d+1)), value=val_diff, key=f"s_{idx}", label_visibility="collapsed")
                        u["task_diffs"][task] = diff
                        if c[2].button("✔️", key=f"v_{idx}"):
                            process_xp_change(100 * diff, "fait"); u["completed_quests"].append(task); save_data(u); st.rerun()
                        if u['mode'] == "Exalté" and len(c) > 3:
                            if c[3].button("❌", key=f"x_{idx}"):
                                process_xp_change(-(100 * diff), "rouge"); save_data(u); st.rerun()
                    idx += 1

# --- TAB 2 : STATISTIQUES ---
with tabs[1]:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>📈 Progression</h3>", unsafe_allow_html=True)
        if u["xp_history"]:
            df = pd.DataFrame(u["xp_history"]); df['date'] = pd.to_datetime(df['date'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp_cumul'], mode='lines', line=dict(color='#00FFCC', width=2), name="XP"))
            for status, color, label in [('fait', '#00FFCC', 'Succès'), ('rouge', 'red', 'Échec')]:
                sub = df[df['status'] == status]
                if not sub.empty: fig.add_trace(go.Scatter(x=sub['date'], y=sub['xp_cumul'], mode='markers', marker=dict(color=color, size=8), name=label))
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>🕸️ Profil de Puissance</h3>", unsafe_allow_html=True)
        fig_r = go.Figure(data=go.Scatterpolar(r=list(u['stats'].values()), theta=list(u['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(u['stats'].values())+10])), template="plotly_dark", height=400, margin=dict(l=40, r=40, t=10, b=10))
        st.plotly_chart(fig_r, use_container_width=True)

# --- TAB 3 : SYSTÈME ---
with tabs[2]:
    cap_q = get_capacity_for_period(u['level'], "Quotidiennes")
    st.subheader("🧩 Architecture")
    st.markdown(f"**Quotidiennes** : {cap_q} slots | **Autres** : 1 slot.")

# --- TAB 4 : CONFIGURATION ---
with tabs[3]:
    new_m = st.radio("Difficulté", ["Séide", "Exalté"], index=["Séide", "Exalté"].index(u["mode"]))
    if new_m != u["mode"]: u["mode"] = new_m; save_data(u); st.rerun()
    st.divider()
    cp, ct, cb = st.columns([1, 2, 1])
    sel_p = cp.selectbox("Période", ["Quotidiennes", "Hebdomadaires", "Mensuelles", "Trimestrielles", "Annuelles"])
    t_add = ct.text_input("Tâche")
    if cb.button("Ajouter"):
        cap_limit = get_capacity_for_period(u['level'], sel_p)
        if len(u["task_lists"].get(sel_p, [])) >= cap_limit: st.error("Limite atteinte.")
        else:
            if t_add and t_add not in [t for sub in u["task_lists"].values() for t in sub]:
                u["task_lists"][sel_p].append(t_add); save_data(u); st.rerun()
    for p, tasks in u["task_lists"].items():
        if tasks:
            st.write(f"**{p}**")
            for i, t in enumerate(tasks):
                cx1, cx2 = st.columns([4, 1])
                cx1.write(f"• {t}")
                if cx2.button("❌", key=f"del_{p}_{i}"): u["task_lists"][p].remove(t); save_data(u); st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⏳ Temps")
    if st.button("⏭️ SAUTER UN JOUR"):
        if u['mode'] == "Exalté": process_xp_change(-(len(u["task_lists"].get("Quotidiennes", [])) * 100), "rouge")
        u["internal_date"] = (datetime.strptime(u["internal_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        u["completed_quests"] = [q for q in u["completed_quests"] if q not in u["task_lists"].get("Quotidiennes", [])]
        save_data(u); st.rerun()
    st.header("🔄 Resets")
    for p in u["task_lists"].keys():
        if st.button(f"Reset {p}"):
            u["completed_quests"] = [q for q in u["completed_quests"] if q not in u["task_lists"].get(p, [])]
            save_data(u); st.rerun()
    st.divider()
    if st.button("💀 HARD RESET", type="primary"): u = get_default_data(); save_data(u); st.rerun()
