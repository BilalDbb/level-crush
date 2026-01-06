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
            # Nettoyage structurel
            if "task_diffs" in d: del d["task_diffs"]
            if "stats" in d: del d["stats"]
            return d
    except: pass
    return get_default_data()

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

u = load_data()

# --- 4. CSS & THÈME ---
# Palette plus douce et lisible
PALETTE = {
    "Sombre": {
        "bg": "#121212",           # Gris très foncé (pas noir complet)
        "card_bg": "#2D2D2D",      # Gris anthracite
        "text": "#E0E0E0",         # Blanc cassé (plus doux)
        "sub_text": "#A0A0A0",
        "border": "#404040",
        "accent": "#00ADB5"        # Cyan soft
    },
    "Clair": {
        "bg": "#F5F7FA",
        "card_bg": "#FFFFFF",
        "text": "#2C3E50",
        "sub_text": "#7F8C8D",
        "border": "#E1E8ED",
        "accent": "#2980B9"
    }
}
P = PALETTE[u.get("theme", "Sombre")]

st.set_page_config(page_title="LEVEL CRUSH", layout="wide")

st.markdown(f"""
    <style>
    /* Global Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Source Sans Pro', sans-serif;
        color: {P['text']};
    }}
    .stApp {{
        background-color: {P['bg']};
    }}
    
    /* Card Design */
    .task-card {{
        background-color: {P['card_bg']};
        border: 1px solid {P['border']};
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
    }}
    
    /* Typography */
    .task-title {{
        font-size: 16px;
        font-weight: 500;
        color: {P['text']};
        margin-left: 10px;
    }}
    .task-title-done {{
        font-size: 16px;
        color: {P['sub_text']}; /* Gris pour tâche finie */
        margin-left: 10px;
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {P['card_bg']};
        color: {P['text']};
        border: 1px solid {P['border']};
        border-radius: 6px;
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        border-color: {P['accent']};
        color: {P['accent']};
    }}
    
    /* Progress Bar */
    .stProgress > div > div > div > div {{
        background-color: {P['accent']};
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIQUE MÉTIER ---
def process_xp_change(amount, task_name=None, type="action"):
    u['xp'] += amount
    
    # Level Up
    leveled_up = False
    while True:
        req = get_xp_required(u['level'])
        if u['xp'] >= req and u['level'] < 100:
            u['xp'] -= req
            u['level'] += 1
            leveled_up = True
            st.toast(f"🔥 LEVEL UP! NIVEAU {u['level']} 🔥")
        else: break
        
    # Level Down (Exalté)
    if u['mode'] == "Exalté" and u['xp'] < 0 and u['level'] > 1:
        u['level'] -= 1
        u['xp'] += get_xp_required(u['level'])
        st.toast("📉 LEVEL DOWN...")

    # Log
    time_str = datetime.now().strftime("%H:%M")
    if task_name:
        log_txt = f"{time_str} | {task_name} ({amount:+d} XP)"
        u["combat_log"].insert(0, log_txt)
        u["combat_log"] = u["combat_log"][:15]
    
    # Historique Level Up
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
    st.title("⚔️ LEVEL CRUSH")

with c_lvl:
    st.markdown(f"""
    <div style="text-align:right; padding-top:10px;">
        <span style="font-size:1.6em; font-weight:bold; color:{title_color};">NIV. {u['level']}</span><br>
        <span style="font-size:0.9em; color:{P['sub_text']}; text-transform:uppercase; letter-spacing:1px;">{title_name}</span>
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
    
    if tsks:
        for i, t in enumerate(tsks):
            done = t in u["completed_quests"]
            
            # Utilisation d'un container pour isoler la ligne
            with st.container():
                # On utilise des colonnes fixes pour éviter le décalage (Shift)
                # Col 1 : Bouton (Action) ou Icone (Etat)
                # Col 2 : Texte
                c_btn, c_txt = st.columns([0.1, 0.9])
                
                with c_btn:
                    if not done:
                        # Bouton vide pour valider
                        if st.button("⬜", key=f"check_{i}"):
                            process_xp_change(XP_PER_TASK, t)
                            u["completed_quests"].append(t)
                            save_data(u)
                            st.rerun()
                    else:
                        # Simple icône si fait (prend la même place que le bouton)
                        st.markdown("<div style='text-align:center; padding-top:5px;'>✅</div>", unsafe_allow_html=True)
                
                with c_txt:
                    # Gestion du style du texte via CSS class
                    if done:
                        st.markdown(f"<div class='task-title-done'>{t}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='task-title'>{t}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<hr style='margin:5px 0; border-color:{P['border']}; opacity:0.3;'>", unsafe_allow_html=True)
                
    else:
        st.info("Aucune quête active. Ajoutez-en via l'onglet Config.")

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
        
        # Ligne principale
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['xp_cumul'], 
            mode='lines', 
            line=dict(color=P['text'], width=2), 
            showlegend=False
        ))
        
        # Config des points et légendes
        # daily_0 = Aucune tâche
        # daily_partial = Partiel
        # daily_100 = 100%
        # level_up = Noir (ou spécial)
        
        colors = {'daily_0': '#E74C3C', 'daily_partial': '#F39C12', 'daily_100': '#2ECC71', 'level_up': '#000000'}
        names = {
            'daily_0': 'Aucune tâche réalisée', 
            'daily_partial': 'Tâches partiellement réalisées', 
            'daily_100': '100% Fait', 
            'level_up': 'LEVEL UP'
        }
        
        for status_type in colors.keys():
            subset = df[df['status'] == status_type]
            if not subset.empty:
                # Bordure blanche autour des points pour qu'ils ressortent sur fond sombre
                fig.add_trace(go.Scatter(
                    x=subset['date'], 
                    y=subset['xp_cumul'], 
                    mode='markers', 
                    marker=dict(color=colors[status_type], size=10, line=dict(width=2, color='white')),
                    name=names[status_type]
                ))

        # Adaptation du graph au thème
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=P['text']),
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=1.1, font=dict(size=10)),
            xaxis=dict(showgrid=False, linecolor=P['border']),
            yaxis=dict(showgrid=True, gridcolor=P['border'], zerolinecolor=P['border'])
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Pas encore d'historique.")

with tabs[2]:
    st.subheader("Paramètres")
    
    c_theme, c_mode = st.columns(2)
    with c_theme:
        new_theme = st.radio("Thème", ["Sombre", "Clair"], index=["Sombre", "Clair"].index(u.get("theme", "Sombre")))
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
    
    # Bouton Fin de Journée
    if st.button("🌙 Fin de journée (Bilan)"):
        # 1. Calcul Statut
        total = len(u["task_lists"]["Quotidiennes"])
        done_count = len(u["completed_quests"])
        
        status_key = "daily_partial"
        if total > 0:
            if done_count == 0: status_key = "daily_0"
            elif done_count == total: status_key = "daily_100"
            else: status_key = "daily_partial"
        else:
            status_key = "daily_partial" # Par défaut si pas de tâches
        
        # 2. Sauvegarde Historique
        u["xp_history"].append({
            "date": u["internal_date"],
            "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']),
            "status": status_key
        })
        
        # 3. Pénalité Exalté
        if u['mode'] == "Exalté":
            missed = total - done_count
            if missed > 0:
                pen = missed * XP_PER_TASK
                process_xp_change(-pen, "Journée incomplète")

        # 4. Passage au lendemain + Reset
        u["internal_date"] = (datetime.strptime(u["internal_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        u["completed_quests"] = []
        save_data(u)
        st.rerun()

    st.divider()
    if st.button("💀 HARD RESET"):
        save_data(get_default_data())
        st.rerun()
