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
            # Nettoyage
            if "task_diffs" in d: del d["task_diffs"]
            if "stats" in d: del d["stats"]
            return d
    except: pass
    return get_default_data()

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

u = load_data()

# --- 4. CSS & THÈME (CORRIGÉ & HAUT CONTRASTE) ---
PALETTE = {
    "Sombre": {
        "bg": "#0E1117",           # Fond Streamlit standard foncé
        "card_bg": "#262730",      # Carte Gris Soutenu (plus clair que le fond)
        "text": "#FFFFFF",         # BLANC PUR
        "sub_text": "#CCCCCC",     # Gris très clair
        "border": "#41444C",       # Bordure visible
        "accent": "#FF4B4B",       # Rouge Streamlit ou autre
        "success": "#00CC96"       # Vert
    },
    "Clair": {
        "bg": "#FFFFFF",
        "card_bg": "#F0F2F6",
        "text": "#000000",
        "sub_text": "#555555",
        "border": "#D1D5DB",
        "accent": "#FF4B4B",
        "success": "#00CC96"
    }
}
P = PALETTE[u.get("theme", "Sombre")]

st.set_page_config(page_title="LEVEL CRUSH", layout="wide")

# Injection CSS agressif pour forcer les couleurs
st.markdown(f"""
    <style>
    /* Forçage global des textes */
    html, body, .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, li, span {{
        color: {P['text']} !important;
        font-family: 'Source Sans Pro', sans-serif;
    }}
    
    .stApp {{
        background-color: {P['bg']};
    }}
    
    /* Carte Tâche */
    .task-card {{
        background-color: {P['card_bg']};
        border: 1px solid {P['border']};
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        /* Ombre légère pour détacher du fond */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    
    /* Titre Tâche */
    .task-title {{
        font-size: 18px; /* Un peu plus gros */
        font-weight: 600;
        color: {P['text']} !important;
        margin-left: 12px;
    }}
    
    .task-title-done {{
        font-size: 18px;
        font-weight: 400;
        color: {P['sub_text']} !important;
        text-decoration: none; /* Pas barré comme demandé */
        margin-left: 12px;
        opacity: 0.7;
    }}
    
    /* Boutons */
    div.stButton > button {{
        background-color: {P['card_bg']};
        color: {P['text']};
        border: 1px solid {P['border']};
        font-weight: bold;
    }}
    div.stButton > button:hover {{
        border-color: {P['text']};
        color: {P['text']};
        background-color: {P['border']};
    }}
    
    /* Input Text */
    div.stTextInput > div > div > input {{
        background-color: {P['card_bg']};
        color: {P['text']};
    }}
    
    /* Radio Buttons Label */
    .stRadio label {{
        color: {P['text']} !important;
    }}
    
    /* Tabs */
    button[data-baseweb="tab"] {{
        color: {P['sub_text']};
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {P['text']};
        font-weight: bold;
    }}

    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIQUE MÉTIER ---
def process_xp_change(amount, task_name=None, type="action"):
    u['xp'] += amount
    
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
        st.toast("📉 LEVEL DOWN...")

    time_str = datetime.now().strftime("%H:%M")
    if task_name:
        log_txt = f"{time_str} | {task_name} ({amount:+d} XP)"
        u["combat_log"].insert(0, log_txt)
        u["combat_log"] = u["combat_log"][:15]
    
    if leveled_up:
        u["xp_history"].append({
            "date": u["internal_date"], 
            "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']), 
            "status": "level_up"
        })

# --- 6. HEADER ---
c_title, c_lvl = st.columns([2, 1])
curr_l_req, title_name, title_color = get_current_title_info(u['level'])

with c_title:
    st.title("⚔️ LEVEL CRUSH")

with c_lvl:
    # Utilisation de st.metric pour un rendu natif propre en haut à droite
    st.markdown(f"""
    <div style="background:{P['card_bg']}; border:1px solid {P['border']}; border-radius:10px; padding:10px; text-align:center;">
        <span style="color:{title_color}; font-size:1.4em; font-weight:bold;">NIV. {u['level']}</span><br>
        <span style="color:{P['sub_text']}; font-size:0.8em; letter-spacing:1px;">{title_name.upper()}</span>
    </div>
    """, unsafe_allow_html=True)

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
            
            # Utilisation de container pour lier le CSS
            with st.container():
                # Layout en colonnes fixes
                # Col 1 (Petite) : Checkbox/Statut
                # Col 2 (Grande) : Texte
                c_btn, c_txt = st.columns([0.15, 0.85])
                
                with c_btn:
                    if not done:
                        # Bouton vide simple
                        if st.button("⬜", key=f"check_{i}"):
                            process_xp_change(XP_PER_TASK, t)
                            u["completed_quests"].append(t)
                            save_data(u)
                            st.rerun()
                    else:
                        # Icone centrée
                        st.markdown(f"<div style='text-align:center; font-size:1.2em; color:{P['success']}; padding-top:8px;'>✔</div>", unsafe_allow_html=True)
                
                with c_txt:
                    # Affichage du texte
                    # On utilise du HTML brut pour être sûr du rendu visuel
                    # Padding top pour aligner avec le bouton
                    style_class = "task-title-done" if done else "task-title"
                    st.markdown(f"""
                        <div class="task-card">
                            <span class="{style_class}">{t}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
    else:
        st.info("Aucune quête active. Ajoutez-en via l'onglet Config.")

    with st.expander("📜 Journal de Bord"):
        for log in u["combat_log"]:
            st.caption(log)

with tabs[1]:
    st.subheader("Performance")
    
    if u["xp_history"]:
        df = pd.DataFrame(u["xp_history"])
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        
        # Courbe principale (Blanche pour fort contraste)
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['xp_cumul'], 
            mode='lines', 
            line=dict(color=P['text'], width=3), 
            showlegend=False
        ))
        
        # Points et Légende mise à jour
        colors = {'daily_0': '#FF4B4B', 'daily_partial': '#FFAA00', 'daily_100': '#00CC96', 'level_up': '#FFFFFF'}
        # Légendes renommées selon ta demande
        names = {
            'daily_0': 'Aucune tâche réalisée', 
            'daily_partial': 'Tâches partiellement réalisées', 
            'daily_100': '100% Fait', 
            'level_up': 'LEVEL UP'
        }
        
        for status_type in colors.keys():
            subset = df[df['status'] == status_type]
            if not subset.empty:
                # Si Level Up, point noir avec bord blanc pour contraste max
                line_color = '#000000' if status_type == 'level_up' else 'white'
                fill_color = colors[status_type]
                
                fig.add_trace(go.Scatter(
                    x=subset['date'], 
                    y=subset['xp_cumul'], 
                    mode='markers', 
                    marker=dict(color=fill_color, size=12, line=dict(width=2, color=line_color)),
                    name=names[status_type]
                ))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=P['text'], size=12),
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=1.15),
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
    
    with st.form("add"):
        c_in, c_bt = st.columns([3, 1])
        new_t = c_in.text_input("Nouvelle Quête", placeholder="Ex: Lire 10 pages")
        if c_bt.form_submit_button("Ajouter") and new_t:
            u["task_lists"]["Quotidiennes"].append(new_t)
            save_data(u)
            st.rerun()

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

with st.sidebar:
    st.header("⏳ Temps")
    
    if st.button("🌙 Fin de journée (Bilan)"):
        total = len(u["task_lists"]["Quotidiennes"])
        done_count = len(u["completed_quests"])
        
        status_key = "daily_partial"
        if total > 0:
            if done_count == 0: status_key = "daily_0"
            elif done_count == total: status_key = "daily_100"
            else: status_key = "daily_partial"
        else: status_key = "daily_partial"
        
        u["xp_history"].append({
            "date": u["internal_date"],
            "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']),
            "status": status_key
        })
        
        if u['mode'] == "Exalté":
            missed = total - done_count
            if missed > 0:
                pen = missed * XP_PER_TASK
                process_xp_change(-pen, "Journée incomplète")

        u["internal_date"] = (datetime.strptime(u["internal_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        u["completed_quests"] = []
        save_data(u)
        st.rerun()

    st.divider()
    if st.button("💀 HARD RESET"):
        save_data(get_default_data())
        st.rerun()
