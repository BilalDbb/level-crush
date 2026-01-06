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

def get_default_data():
    return {
        "level": 1, "xp": 0, "mode": "Séide", 
        "stats": {"Physique": 0, "Connaissances": 0, "Autonomie": 0, "Mental": 0}, 
        "completed_quests": [], 
        "task_lists": {"Quotidiennes": [], "Hebdomadaires": [], "Mensuelles": [], "Trimestrielles": [], "Annuelles": []}, 
        "task_diffs": {}, "task_stat_links": {}, "combat_log": [], "xp_history": [], "internal_date": datetime.now().strftime("%Y-%m-%d")
    }

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
            # Assurer les clés de stats par défaut si manquantes
            for s in ["Physique", "Connaissances", "Autonomie", "Mental"]:
                if s not in d["stats"]: d["stats"][s] = 0
            return d
    except: pass
    return get_default_data()

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

u = load_data()

def process_xp_change(amount, task_name=None, status="fait"):
    u['xp'] += amount
    log_msg = f"{status.upper()} : {task_name if task_name else 'Action'} ({amount:+d} XP)"
    if status == "fait" and task_name in u["task_stat_links"]:
        stat_name = u["task_stat_links"][task_name]
        gain_stat = u["task_diffs"].get(task_name, 1)
        u["stats"][stat_name] = round(u["stats"][stat_name] + gain_stat, 1)
        log_msg += f" | +{gain_stat} {stat_name}"
    while True:
        req = get_xp_required(u['level'])
        if u['xp'] >= req and u['level'] < 100: u['xp'] -= req; u['level'] += 1; st.toast("🌟 LEVEL UP !")
        else: break
    if u['mode'] == "Exalté":
        while u['xp'] < 0 and u['level'] > 1: u['level'] -= 1; u['xp'] += get_xp_required(u['level']); st.toast("📉 LEVEL DOWN...")
    u["xp_history"].append({"date": u["internal_date"], "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']), "status": status})
    u["combat_log"].insert(0, f"[{u['internal_date']}] {log_msg}")
    u["combat_log"] = u["combat_log"][:10] # Garder un peu plus d'historique

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
    
    # --- MODIFICATION : Affichage uniquement Quotidiennes ---
    # Les autres sont techniquement là (dans u["task_lists"]) mais on ne les boucle pas.
    q_p = "Quotidiennes"
    tsks = u["task_lists"].get(q_p, [])
    
    st.subheader(f"📅 Quotidien ({len(tsks)}/{get_capacity_for_period(u['level'], q_p)})")
    
    if tsks:
        idx = 0
        for t in tsks:
            done = t in u["completed_quests"]
            c = st.columns([2, 1, 0.5, 0.5] if u['mode'] == "Exalté" else [2, 1, 1])
            c[0].markdown(f"{'✅' if done else '🔳'} {t} <small style='color:#666'>({u['task_stat_links'].get(t, 'N/A')})</small>", unsafe_allow_html=True)
            if not done:
                cur_w = u["task_diffs"].get(t, 1)
                # Limite visuelle du poids à 3 pour les dailies
                d = c[1].select_slider("Poids", options=[1, 2, 3], value=min(cur_w, 3), key=f"s_{idx}", label_visibility="collapsed")
                u["task_diffs"][t] = d
                if c[2].button("✔️", key=f"v_{idx}"): process_xp_change(100 * d, t, "fait"); u["completed_quests"].append(t); save_data(u); st.rerun()
                if u['mode'] == "Exalté" and len(c) > 3:
                    if c[3].button("❌", key=f"x_{idx}"): process_xp_change(-(100 * d), t, "rouge"); save_data(u); st.rerun()
            idx += 1
    else:
        st.info("Aucune tâche quotidienne configurée.")

    st.subheader("🛡️ Journal de Bord") # Rename
    for log in u["combat_log"]: st.caption(log)

with tabs[1]:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("<h3 style='text-align:center;'>📈 Progression</h3>", unsafe_allow_html=True)
        if u["xp_history"]:
            df = pd.DataFrame(u["xp_history"]); df['date'] = pd.to_datetime(df['date'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['xp_cumul'], mode='lines', line=dict(color='#00FFCC', width=2), name="Courbe XP"))
            # --- MODIFICATION : Rename 'Echec/Saut' en 'Echec' ---
            for s, col, lab in [('fait', '#00FFCC', 'Succès'), ('rouge', 'red', 'Echec')]:
                sub = df[df['status'] == s]
                if not sub.empty: fig.add_trace(go.Scatter(x=sub['date'], y=sub['xp_cumul'], mode='markers', marker=dict(color=col, size=8), name=lab))
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.markdown("<h3 style='text-align:center;'>🕸️ Équilibre du Jour</h3>", unsafe_allow_html=True)
        # --- MODIFICATION RADAR : Calcul 0-100% basé sur les tâches du jour ---
        stats_categories = ["Physique", "Connaissances", "Autonomie", "Mental"]
        daily_tasks = u["task_lists"].get("Quotidiennes", [])
        
        # Calcul des % par catégorie
        cat_total_weight = {k: 0 for k in stats_categories}
        cat_done_weight = {k: 0 for k in stats_categories}
        
        for t in daily_tasks:
            cat = u["task_stat_links"].get(t, "Physique")
            w = u["task_diffs"].get(t, 1)
            if cat in stats_categories:
                cat_total_weight[cat] += w
                if t in u["completed_quests"]:
                    cat_done_weight[cat] += w
        
        r_values = []
        hover_texts = []
        
        for cat in stats_categories:
            if cat_total_weight[cat] > 0:
                val = (cat_done_weight[cat] / cat_total_weight[cat]) * 100
            else:
                val = 0
            r_values.append(val)
            
            # Légende demandée
            if val == 0: txt = "Non commencé"
            elif val == 100: txt = "Maîtrisé"
            else: txt = "Partiel"
            hover_texts.append(txt)

        fig_r = go.Figure(data=go.Scatterpolar(
            r=r_values, 
            theta=stats_categories, 
            fill='toself', 
            line_color='#00FFCC',
            hovertext=hover_texts,
            hovertemplate="%{theta}: %{r:.0f}%<br>Statut: %{hovertext}<extra></extra>"
        ))
        
        # Axe forcé 0-100
        fig_r.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
            template="plotly_dark", 
            height=400
        )
        st.plotly_chart(fig_r, use_container_width=True)

with tabs[2]:
    st.subheader("🧩 Architecture du Système")
    st.markdown(f"""
    **📏 Capacité & Quotas**
    - **Quotidiennes** : {get_capacity_for_period(u['level'], 'Quotidiennes')} slots (Base: 4 | +1 par 20 lvls).
    **🧬 Évolution**
    Chaque succès augmente vos statistiques et votre niveau global.
    """)

with tabs[3]:
    st.subheader("⚙️ Configuration")
    nm = st.radio("Mode de Jeu", ["Séide", "Exalté"], index=["Séide", "Exalté"].index(u["mode"]), help="Séide: Pas de pénalité. Exalté: Perte d'XP possible.")
    if nm != u["mode"]: u["mode"] = nm; save_data(u); st.rerun()
    st.divider()
    
    # --- MODIFICATION : Suppression du choix de la période (Force Daily) ---
    cp, cs, cb = st.columns([2, 1, 0.5])
    sel_p = "Quotidiennes" # Hardcodé
    
    t_add = cp.text_input("Nouvelle tâche (Quotidienne)")
    st_link = cs.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"])
    
    if cb.button("➕"):
        cap = get_capacity_for_period(u['level'], sel_p)
        if len(u["task_lists"].get(sel_p, [])) >= cap: st.error(f"Limite atteinte pour {sel_p} ({cap} slots).")
        elif t_add and t_add not in u["task_stat_links"]:
            u["task_lists"][sel_p].append(t_add); u["task_stat_links"][t_add] = st_link; save_data(u); st.rerun()
    
    # Affichage uniquement de la liste quotidienne pour édition
    tsks = u["task_lists"].get(sel_p, [])
    if tsks:
        st.write(f"**Édition des tâches actives**")
        for i, t in enumerate(tsks):
            cx1, cx2, cx3 = st.columns([2, 1, 1])
            nn = cx1.text_input("Nom", t, key=f"n_{sel_p}_{i}", label_visibility="collapsed")
            ns = cx2.selectbox("Stat", ["Physique", "Connaissances", "Autonomie", "Mental"], index=["Physique", "Connaissances", "Autonomie", "Mental"].index(u['task_stat_links'].get(t, "Physique")), key=f"s_{sel_p}_{i}", label_visibility="collapsed")
            c_bt = cx3.columns(2)
            if c_bt[0].button("💾", key=f"sv_{sel_p}_{i}"):
                if nn != t:
                    u["task_lists"][sel_p][i] = nn
                    u["task_stat_links"][nn] = u["task_stat_links"].pop(t)
                    if t in u["task_diffs"]: u["task_diffs"][nn] = u["task_diffs"].pop(t)
                u["task_stat_links"][nn] = ns; save_data(u); st.rerun()
            if c_bt[1].button("❌", key=f"dl_{sel_p}_{i}"): u["task_lists"][sel_p].remove(t); u["task_stat_links"].pop(t, None); save_data(u); st.rerun()

with st.sidebar:
    st.header("⏳ Temps")
    if st.button("⏭️ SAUTER UN JOUR"):
        # Reset uniquement sur les quotidiennes
        if u['mode'] == "Exalté": process_xp_change(-(len(u["task_lists"].get("Quotidiennes", [])) * 100), "Saut de jour", "rouge")
        else: process_xp_change(0, "Saut de jour", "rouge")
        u["internal_date"] = (datetime.strptime(u["internal_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        u["completed_quests"] = [q for q in u["completed_quests"] if q not in u["task_lists"].get("Quotidiennes", [])]; save_data(u); st.rerun()
    
    # Suppression des boutons de reset spécifiques, garder juste un Reset Daily manuel si besoin
    if st.button("Reset Quotidiennes (Même jour)"):
        u["completed_quests"] = [q for q in u["completed_quests"] if q not in u["task_lists"].get("Quotidiennes", [])]; save_data(u); st.rerun()
        
    st.divider()
    if st.button("💀 HARD RESET"): save_data(get_default_data()); st.rerun()
