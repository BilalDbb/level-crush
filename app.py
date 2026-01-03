import streamlit as st
import streamlit.components.v1 as components
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

# --- 3. CONFIGURATION DES TITRES ---
TITLES_DATA = [(1, "Starter", "#DCDDDF"), (3, "Néophyte", "#3498DB"), (6, "Aspirant", "#2ECC71"), (10, "Soldat de Plomb", "#E67E22"), (14, "Gardien de Fer", "#95A5A6"), (19, "Traqueur Silencieux", "#9B59B6"), (24, "Vanguard", "#2980B9"), (30, "Chevalier d'Acier", "#BDC3C7"), (36, "Briseur de Chaînes", "#F39C12"), (43, "Architecte du Destin", "#34495E"), (50, "Légat du Système", "#16A085"), (58, "Commandeur", "#27AE60"), (66, "Seigneur de Guerre", "#C0392B"), (75, "Entité Transcendante", "#F1C40F"), (84, "Demi-Dieu", "#E74C3C"), (93, "Souverain", "#8E44AD"), (100, "LEVEL CRUSHER", "#000000")]

def get_current_title_info(lvl):
    current = TITLES_DATA[0]
    for l_req, name, color in TITLES_DATA:
        if lvl >= l_req: current = (l_req, name, color)
    return current

# --- 4. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 
def load_data():
    try:
        res = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if res.data:
            d = res.data[0]['data']
            if isinstance(d, str): d = json.loads(d)
            for k in ["combat_log", "task_stat_links", "task_diffs"]:
                if k not in d: d[k] = [] if k=="combat_log" else {}
            return d
    except: pass
    return {"level": 1, "xp": 0, "mode": "Séide", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, "task_diffs": {}, "task_stat_links": {}, "combat_log": [], "xp_history": [], "internal_date": "2026-01-03"}

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

u = load_data()

def process_xp_change(amount, task_name=None, status="fait"):
    u['xp'] += amount
    log_msg = f"{status.upper()} : {task_name if task_name else 'Inconnu'} ({amount:+d} XP)"
    if status == "fait" and task_name in u["task_stat_links"]:
        stat_name = u["task_stat_links"][task_name]
        poids = u["task_diffs"].get(task_name, 1)
        gain_stat = round(poids * 0.1, 2)
        u["stats"][stat_name] = round(u["stats"][stat_name] + gain_stat, 2)
        log_msg += f" | +{gain_stat} {stat_name}"
    while True:
        req = get_xp_required(u['level'])
        if u['xp'] >= req and u['level'] < 100: u['xp'] -= req; u['level'] += 1; st.toast("🌟 LEVEL UP !")
        else: break
    if u['mode'] == "Exalté":
        while u['xp'] < 0 and u['level'] > 1: u['level'] -= 1; u['xp'] += get_xp_required(u['level']); st.toast("📉 LEVEL DOWN...")
    u["xp_history"].append({"date": u["internal_date"], "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']), "status": status})
    u["combat_log"].insert(0, f"[{u['internal_date']}] {log_msg}")
    u["combat_log"] = u["combat_log"][:5]

# --- 5. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", layout="wide")
curr_l_req, title_name, title_color = get_current_title_info(u['level'])
glow_color = "#00FFCC" if title_name == "LEVEL CRUSHER" else title_color

st.markdown(f'<div style="text-align:center;padding:10px;"><span style="color:white;font-size:1.1em;">NIV.{u["level"]}</span> <div style="display:inline-block;margin-left:12px;padding:4px 18px;border:2px solid {glow_color};border-radius:20px;box-shadow:0 0 12px {glow_color};background:{title_color};"><b style="color:{"black" if title_name=="Starter" else "#00FFCC" if title_name=="LEVEL CRUSHER" else "white"};font-size:1.3em;">{title_name}</b></div></div>', unsafe_allow_html=True)

tabs = st.tabs(["⚔️ Quêtes", "📊 Statistiques", "🧩 Système", "⚙️ Configuration"])

with tabs[0]:
    req_xp = get_xp_required(u['level'])
    st.progress(min(max(u['xp']/req_xp, 0.0), 1.0))
    st.write(f"XP : **{u['xp']} / {req_xp}**")
    with st.expander("📜 Registre des Rangs", expanded=False):
        items_html = "".join([f'<div style="min-width:90px;text-align:center;opacity:{"1" if u["level"]>=l else "0.3"};margin-right:15px;"><div class="{"pulse-active" if curr_l_req==l else ""}" style="width:14px;height:14px;background:{"#333" if u["level"]<l else c};border-radius:50%;margin:0 auto;border:2px solid {"white" if curr_l_req==l else "transparent"};"></div><p style="font-size:11px;color:{"#333" if u["level"]<l else c};margin-top:8px;font-weight:bold;">{n if u["level"]>=l else "???"}</p><p style="font-size:9px;color:#666;">Niv.{l}</p></div>' for l,n,c in TITLES_DATA])
        components.html(f'<style>body{{background:transparent;margin:0;}}@keyframes pulse-anim{{0%{{box-shadow:0 0 0 0 {glow_color}77;}}70%{{box-shadow:0 0 0 8px {glow_color}00;}}100%{{box-shadow:0 0 0 0 {glow_color}00;}}}}.pulse-active{{animation:pulse-anim 2s infinite;}}.scroll{{display:flex;overflow-x:auto;padding:20px 5px;scrollbar-width:thin;}}</style><div class="scroll">{items_html}</div>', height=110)
    st.divider()
    idx = 0
    for q_p in ["Quotidiennes", "Hebdomadaires", "Mensuelles", "Trimestrielles", "Annuelles"]:
        tasks = u["task_lists"].get(q_p, [])
        if tasks:
            max_p = {"Quotidiennes":3, "Hebdomadaires":5, "Mensuelles":7, "Trimestrielles":9, "Annuelles":11}[q_p]
            with st.expander(f"{q_p} ({len(tasks)}/{get_capacity_for_period(u['level'], q_p)})", expanded=True):
                for t in tasks:
                    done = t in u["completed_quests"]
                    c = st.columns([2, 1, 0.5, 0.5] if u['mode'] == "Exalté" else [2, 1, 1])
                    c[0].markdown(f"{'✅' if done else '🔳'} {t} <small style='color:#666'>({u['task_stat_links'].get(t, 'N/A')})</small>", unsafe_allow_html=True)
                    if not done:
                        # SECURITE : Recalage du poids si hors limites Catégorie
                        current_weight = u["task_diffs"].get(t, 1)
                        if current_weight > max_p: current_weight = max_p
                        
                        d = c[1].select_slider("Poids", options=list(range(1, max_p+1)), value=current_weight, key=f"s_{idx}", label_visibility="collapsed")
                        u["task_diffs"][t] = d
                        if c[2].button("✔️", key=f"v_{idx}"): process_xp_change(100 * d, t, "fait"); u["completed_quests"].append(t); save_data(u); st.rerun()
                        if u['mode'] == "Exalté" and len(c) > 3:
                            if c[3].button("❌", key=f"x_{idx}"): process_xp_change(-(100 * d), t, "rouge"); save_data(u); st.rerun()
                    idx += 1
    st.subheader("🛡️ Journal de Combat")
    for log in u["combat_log"]: st.caption(log)

with tabs[1]:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("<h3 style='text-align:center;'>📈 Progression</h3>", unsafe_allow_html=True)
        if u["xp_history"]:
            df = pd.DataFrame(u["xp_history"]); df['date'] = pd.to_datetime(df['date'])
            fig = go.Figure(go.Scatter(x=df['date'], y=df['xp_cumul'], mode='lines+markers', line=dict(color='#00FFCC'), name="XP"))
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("<h3 style='text-align:center;'>🕸️ Profil de Puissance</h3>", unsafe_allow_html=True)
        fig_r = go.Figure(data=go.Scatterpolar(r=list(u['stats'].values()), theta=list(u['stats'].keys()), fill='toself', line_color='#00FFCC'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(u['stats'].values())+5])), template="plotly_dark", height=400)
        st.plotly_chart(fig_r, use_container_width=True)

with tabs[2]:
    st.subheader("🧩 Architecture du Système")
    st.markdown(f"""
    **📏 Capacité & Quotas**
    - **Quotidiennes** : {get_capacity_for_period(u['level'], 'Quotidiennes')} slots (Base: 4 | +1 par 20 lvls).
    - **Autres** : 1 slot fixe.
    
    **⚖️ Échelle des Poids (Multiplicateurs)**
    - Quotidiennes : 1 à 3
    - Hebdo : 1 à 5
    - Mensuelles : 1 à 7
    - Trimestrielles : 1 à 9
    - Annuelles : 1 à 11
    
    **🧬 Évolution du Radar**
    Chaque succès rapporte `+ (Poids x 0.1)` dans la statistique liée.
    """)

with tabs[3]:
    st.subheader("⚙️ Configuration des Tâches")
    cp, ct, cs, cb = st.columns([1, 1.5, 1, 0.5])
    sel_p = cp.selectbox("Période", ["Quotidiennes", "Hebdomadaires", "Mensuelles", "Trimestrielles", "Annuelles"])
    t_add = ct.text_input("Tâche")
    stat_link = cs.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"])
    if cb.button("➕"):
        cap = get_capacity_for_period(u['level'], sel_p)
        if len(u["task_lists"].get(sel_p, [])) >= cap: st.error(f"Limite atteinte pour {sel_p} ({cap} slots).")
        elif t_add and t_add not in u["task_stat_links"]:
            u["task_lists"][sel_p].append(t_add); u["task_stat_links"][t_add] = stat_link; save_data(u); st.rerun()
    
    for p, tasks in u["task_lists"].items():
        if tasks:
            st.write(f"**{p}**")
            for i, t in enumerate(tasks):
                cx1, cx2, cx3 = st.columns([2, 1, 1])
                new_name = cx1.text_input("Nom", value=t, key=f"edit_n_{p}_{i}", label_visibility="collapsed")
                new_stat = cx2.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"], index=["Physique", "Connaissances", "Autonomie", "Mental"].index(u['task_stat_links'].get(t, "Physique")), key=f"edit_s_{p}_{i}", label_visibility="collapsed")
                c_btn = cx3.columns(2)
                if c_btn[0].button("💾", key=f"save_{p}_{i}"):
                    if new_name != t:
                        u["task_lists"][p][i] = new_name
                        u["task_stat_links"][new_name] = u["task_stat_links"].pop(t)
                        if t in u["task_diffs"]: u["task_diffs"][new_name] = u["task_diffs"].pop(t)
                    u["task_stat_links"][new_name] = new_stat; save_data(u); st.rerun()
                if c_btn[1].button("❌", key=f"del_{p}_{i}"):
                    u["task_lists"][p].remove(t); u["task_stat_links"].pop(t, None); save_data(u); st.rerun()

with st.sidebar:
    st.header("⏳ Temps")
    if st.button("⏭️ SAUTER UN JOUR"):
        if u['mode'] == "Exalté": process_xp_change(-(len(u["task_lists"].get("Quotidiennes", [])) * 100), "Saut de jour", "rouge")
        u["internal_date"] = (datetime.strptime(u["internal_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        u["completed_quests"] = [q for q in u["completed_quests"] if q not in u["task_lists"].get("Quotidiennes", [])]; save_data(u); st.rerun()
    for p in ["Quotidiennes", "Hebdomadaires", "Mensuelles", "Trimestrielles", "Annuelles"]:
        if st.button(f"Reset {p}"):
            if p == "Quotidiennes": u["internal_date"] = (datetime.strptime(u["internal_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            u["completed_quests"] = [q for q in u["completed_quests"] if q not in u["task_lists"].get(p, [])]; save_data(u); st.rerun()
    st.divider()
    if st.button("💀 HARD RESET"): save_data({"level": 1, "xp": 0, "mode": "Séide", "stats": {"Physique": 10, "Connaissances": 10, "Autonomie": 10, "Mental": 10}, "completed_quests": [], "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, "task_diffs": {}, "task_stat_links": {}, "combat_log": [], "xp_history": [], "internal_date": "2026-01-03"}); st.rerun()
