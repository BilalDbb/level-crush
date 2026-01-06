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
XP_PER_TASK = 100

def get_xp_required(lvl):
    next_lvl = lvl + 1
    if lvl < 5: return int(200 * (next_lvl**1.2))
    elif 5 <= lvl < 100: return int(25 * (next_lvl**1.2))
    else: return int(int(25 * (100**1.2)) * 10)

def get_total_cumulated_xp(lvl, current_xp):
    total = 0
    for l in range(1, lvl): total += get_xp_required(l)
    return total + current_xp

TITLES_DATA = [(1, "Starter", "#DCDDDF"), (3, "Néophyte", "#3498DB"), (6, "Aspirant", "#2ECC71"), (10, "Soldat de Plomb", "#E67E22"), (14, "Gardien de Fer", "#95A5A6"), (19, "Traqueur Silencieux", "#9B59B6"), (24, "Vanguard", "#2980B9"), (30, "Chevalier d'Acier", "#BDC3C7"), (36, "Briseur de Chaînes", "#F39C12"), (43, "Architecte du Destin", "#34495E"), (50, "Légat du Système", "#16A085"), (58, "Commandeur", "#27AE60"), (66, "Seigneur de Guerre", "#C0392B"), (75, "Entité Transcendante", "#F1C40F"), (84, "Demi-Dieu", "#E74C3C"), (93, "Souverain", "#8E44AD"), (100, "LEVEL CRUSHER", "#000000")]

def get_current_title_info(lvl):
    current = TITLES_DATA[0]
    for l_req, name, color in TITLES_DATA:
        if lvl >= l_req: current = (l_req, name, color)
    return current

def get_default_data():
    return {
        "level": 1, "xp": 0, "mode": "Séide", "theme": "Sombre",
        "completed_quests": [], "task_lists": {"Quotidiennes": []},
        "combat_log": [], "xp_history": [], "internal_date": datetime.now().strftime("%Y-%m-%d")
    }

# --- 3. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 
def load_data():
    try:
        res = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if res.data:
            d = res.data[0]['data']
            if isinstance(d, str): d = json.loads(d)
            if "theme" not in d: d["theme"] = "Sombre"
            # Migration structure
            if "task_diffs" in d: del d["task_diffs"]
            if "stats" in d: del d["stats"]
            return d
    except: pass
    return get_default_data()

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

u = load_data()

# --- 4. CSS DYNAMIQUE (THEMING) ---
# Définition des palettes
PALETTE = {
    "Sombre": {
        "bg": "#0e1117", "card_bg": "#1e2130", "text": "#ffffff", "border": "#333",
        "success_border": "#00FFCC", "success_bg": "rgba(0, 255, 204, 0.1)"
    },
    "Clair": {
        "bg": "#ffffff", "card_bg": "#f0f2f6", "text": "#000000", "border": "#ddd",
        "success_border": "#00aa88", "success_bg": "rgba(0, 170, 136, 0.1)"
    }
}
P = PALETTE[u.get("theme", "Sombre")]

st.set_page_config(page_title="LEVEL CRUSH", layout="wide")

# Injection CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: {P['bg']}; color: {P['text']}; }}
    .task-card {{
        background-color: {P['card_bg']};
        padding: 15px;
        border-radius: 10px;
        border: 1px solid {P['border']};
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        transition: all 0.3s ease;
    }}
    .task-card.done {{
        border: 1px solid {P['success_border']};
        background-color: {P['success_bg']};
        box-shadow: 0 0 10px {P['success_border']}40;
    }}
    .task-title {{ font-weight: bold; font-size: 1.1em; color: {P['text']}; flex-grow: 1; margin-left: 15px; }}
    .stButton>button {{ border-radius: 8px; border: none; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIQUE MÉTIER ---
def process_xp_change(amount, task_name=None, type="action"):
    u['xp'] += amount
    
    # Level Logic
    leveled_up = False
    while True:
        req = get_xp_required(u['level'])
        if u['xp'] >= req and u['level'] < 100:
            u['xp'] -= req
            u['level'] += 1
            leveled_up = True
            st.toast(f"🔥 LEVEL UP! NIVEAU {u['level']} 🔥")
        else: break
        
    if u['mode'] == "Exalté" and u['xp'] < 0 and u['level'] > 1:
        u['level'] -= 1
        u['xp'] += get_xp_required(u['level'])
        st.toast("💀 LEVEL DOWN...")

    # Log
    time_str = datetime.now().strftime("%H:%M")
    if task_name:
        log_txt = f"{time_str} | {task_name} ({amount:+d} XP)"
        u["combat_log"].insert(0, log_txt)
        u["combat_log"] = u["combat_log"][:15] # Limite journal
    
    # Enregistrement Graphique (Si Level Up, on marque un point noir)
    if leveled_up:
        u["xp_history"].append({
            "date": u["internal_date"], 
            "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']), 
            "status": "level_up"
        })

# --- 6. HEADER ---
c_title, c_lvl = st.columns([3, 1])
curr_l_req, title_name, title_color = get_current_title_info(u['level'])

with c_title:
    st.markdown(f"# ⚔️ LEVEL CRUSH")

with c_lvl:
    st.markdown(f"""
    <div style="text-align:right; padding:10px;">
        <span style="font-size:1.5em; font-weight:bold; color:{title_color};">NIV. {u['level']}</span><br>
        <span style="font-size:0.8em; color:gray; text-transform:uppercase; letter-spacing:2px;">{title_name}</span>
    </div>
    """, unsafe_allow_html=True)

# Barre XP
req_xp = get_xp_required(u['level'])
progress = min(max(u['xp']/req_xp, 0.0), 1.0)
st.progress(progress)

# --- 7. TABS ---
tabs = st.tabs(["🎯 Quêtes", "📈 Evolution", "⚙️ Config"])

with tabs[0]:
    tsks = u["task_lists"].get("Quotidiennes", [])
    completed_count = 0
    
    if tsks:
        for i, t in enumerate(tsks):
            done = t in u["completed_quests"]
            if done: completed_count += 1
            
            # Container HTML pour le style
            css_class = "task-card done" if done else "task-card"
            icon = "🌟" if done else "⚔️"
            
            # Layout avec colonnes Streamlit imbriquées dans le style visuel c'est compliqué
            # On utilise une approche mixte : Style via Markdown, Bouton via Streamlit
            
            col_ui = st.container()
            c1, c2, c3 = col_ui.columns([0.15, 0.75, 0.1])
            
            with c1:
                # Bouton centré et propre
                if not done:
                    if st.button("⬜", key=f"do_{i}"):
                        process_xp_change(XP_PER_TASK, t)
                        u["completed_quests"].append(t)
                        save_data(u)
                        st.rerun()
                else:
                    st.markdown("<div style='text-align:center; font-size:1.5em;'>✅</div>", unsafe_allow_html=True)
            
            with c2:
                # Titre stylisé sans strikethrough
                color_css = P['success_border'] if done else P['text']
                weight = "bold" if done else "normal"
                st.markdown(f"<div style='padding-top:10px; color:{color_css}; font-weight:{weight}; font-size:1.1em;'>{t}</div>", unsafe_allow_html=True)
            
            with c3:
                 if u['mode'] == "Exalté" and not done:
                     if st.button("✖", key=f"fail_{i}", help="Echec (-XP)"):
                        process_xp_change(-XP_PER_TASK, t)
                        save_data(u)
                        st.rerun()
            
            st.markdown("---") # Séparateur fin
    else:
        st.info("Aucune quête. Va dans Config pour en ajouter.")

    # Journal
    with st.expander("📜 Journal de Bord (Dernières actions)"):
        for log in u["combat_log"]:
            st.caption(log)

with tabs[1]:
    st.subheader("Performance")
    
    if u["xp_history"]:
        df = pd.DataFrame(u["xp_history"])
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        
        # 1. La Ligne (Courbe de progression)
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['xp_cumul'], 
            mode='lines', 
            line=dict(color='#444444', width=2), 
            showlegend=False
        ))
        
        # 2. Les Points (Logique de couleur)
        # Rouge: 0%, Orange: 1-99%, Vert: 100%, Noir: Level Up
        
        # On définit les couleurs manuelles pour Plotly
        colors = {'daily_0': '#FF4B4B', 'daily_partial': '#FFAA00', 'daily_100': '#00CC96', 'level_up': '#000000'}
        names = {'daily_0': '0% Fait', 'daily_partial': '1-99% Fait', 'daily_100': '100% Fait', 'level_up': 'LEVEL UP'}
        
        for status_type in colors.keys():
            subset = df[df['status'] == status_type]
            if not subset.empty:
                fig.add_trace(go.Scatter(
                    x=subset['date'], 
                    y=subset['xp_cumul'], 
                    mode='markers', 
                    marker=dict(color=colors[status_type], size=10, line=dict(width=1, color='white')),
                    name=names[status_type]
                ))

        fig.update_layout(
            template="plotly_dark" if u["theme"] == "Sombre" else "plotly_white",
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Pas encore d'historique.")

with tabs[2]:
    st.subheader("Paramètres")
    
    c_theme, c_mode = st.columns(2)
    with c_theme:
        new_theme = st.radio("Thème Visuel", ["Sombre", "Clair"], index=["Sombre", "Clair"].index(u.get("theme", "Sombre")))
        if new_theme != u.get("theme"):
            u["theme"] = new_theme
            save_data(u)
            st.rerun()
            
    with c_mode:
        nm = st.radio("Difficulté", ["Séide", "Exalté"], index=["Séide", "Exalté"].index(u["mode"]))
        if nm != u["mode"]: u["mode"] = nm; save_data(u); st.rerun()

    st.divider()
    
    # Ajout Tâche
    with st.form("add"):
        c_in, c_bt = st.columns([3, 1])
        new_t = c_in.text_input("Nouvelle Quête", placeholder="Ex: Lire 10 pages")
        if c_bt.form_submit_button("Ajouter") and new_t:
            u["task_lists"]["Quotidiennes"].append(new_t)
            save_data(u)
            st.rerun()

    # Gestion Tâches
    st.write("Modifier / Supprimer")
    to_keep = []
    change = False
    for t in u["task_lists"]["Quotidiennes"]:
        c1, c2 = st.columns([4, 1])
        n_val = c1.text_input("Nom", t, key=f"ed_{t}", label_visibility="collapsed")
        if n_val != t:
            to_keep.append(n_val)
            change = True
        elif c2.button("🗑️", key=f"del_{t}"):
            change = True
        else:
            to_keep.append(t)
            
    if change:
        u["task_lists"]["Quotidiennes"] = to_keep
        save_data(u)
        st.rerun()

# --- SIDEBAR (Gestion du Temps) ---
with st.sidebar:
    st.header("⏳ Temps")
    
    if st.button("🌙 Fin de journée (Bilan)"):
        # 1. Calcul du % de réalisation
        total = len(u["task_lists"]["Quotidiennes"])
        done_count = len(u["completed_quests"])
        
        status_key = "daily_partial"
        if total == 0: status_key = "daily_partial" # Cas vide
        elif done_count == 0: status_key = "daily_0"
        elif done_count == total: status_key = "daily_100"
        else: status_key = "daily_partial"
        
        # 2. Sauvegarde Historique avec le bon statut pour la couleur
        u["xp_history"].append({
            "date": u["internal_date"],
            "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']),
            "status": status_key
        })
        
        # 3. Pénalité si Exalté
        if u['mode'] == "Exalté":
            missed = total - done_count
            if missed > 0:
                pen = missed * XP_PER_TASK
                process_xp_change(-pen, "Journée incomplète")

        # 4. Reset
        u["internal_date"] = (datetime.strptime(u["internal_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        u["completed_quests"] = []
        save_data(u)
        st.rerun()

    st.divider()
    if st.button("💀 HARD RESET"):
        save_data(get_default_data())
        st.rerun()
