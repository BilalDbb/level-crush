import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONFIGURATION SUPABASE ---
# Le code va chercher les infos dans le fichier .streamlit/secrets.toml (LOCAL)
# OU dans les Secrets de Streamlit Cloud (EN LIGNE)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    DB_CONNECTED = True
except Exception as e:
    DB_CONNECTED = False
    # On n'affiche l'erreur que si on est en local pour ne pas effrayer l'utilisateur final
    st.warning("Base de données non connectée. Vérifiez le fichier .streamlit/secrets.toml")

# Nom de la table et ID utilisateur
TABLE_NAME = "profiles" 
USER_ID = "shadow_monarch_01"

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Task RPG", page_icon="⚔️")

# --- DATA: TITRES & RANGS ---
TITLES = [
    (1, "Starter", "#DCDDDF"), (3, "Néophyte", "#3498DB"), (6, "Aspirant", "#2ECC71"), 
    (10, "Soldat de Plomb", "#E67E22"), (14, "Gardien de Fer", "#95A5A6"), 
    (19, "Traqueur Silencieux", "#9B59B6"), (24, "Vanguard", "#2980B9"), 
    (30, "Chevalier d'Acier", "#BDC3C7"), (36, "Briseur de Chaînes", "#F39C12"), 
    (43, "Architecte du Destin", "#34495E"), (50, "Légat du Système", "#16A085"), 
    (58, "Commandeur", "#27AE60"), (66, "Seigneur de Guerre", "#C0392B"), 
    (75, "Entité Transcendante", "#F1C40F"), (84, "Demi-Dieu", "#E74C3C"), 
    (93, "Souverain", "#8E44AD"), (100, "LEVEL CRUSHER", "#000000")
]

# --- STYLE CSS ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
    .task-container {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
        border-left: 5px solid #ccc;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- GESTION PERSISTANCE (SUPABASE) ---

def load_data_from_db():
    """Charge les données JSON depuis Supabase dans le session_state"""
    if not DB_CONNECTED: return
    
    try:
        response = supabase.table(TABLE_NAME).select("data").eq("user_id", USER_ID).execute()
        
        if response.data and len(response.data) > 0:
            # Données trouvées, on peuple le session_state
            data = response.data[0]['data']
            st.session_state.tasks = data.get('tasks', [])
            st.session_state.logs = data.get('logs', [])
            st.session_state.user_xp = data.get('user_xp', 0)
            st.session_state.user_lvl = data.get('user_lvl', 1)
            st.session_state.game_mode = data.get('game_mode', "Séide")
            st.session_state.current_date = data.get('current_date', datetime.today().strftime("%Y-%m-%d"))
        else:
            # Pas de données, on initialise une ligne vide
            save_data_to_db() 
            
    except Exception as e:
        st.error(f"Erreur chargement DB: {e}")

def save_data_to_db():
    """Sauvegarde tout l'état actuel dans la colonne JSONB"""
    if not DB_CONNECTED: return

    # On prépare le payload JSON
    payload = {
        "tasks": st.session_state.get('tasks', []),
        "logs": st.session_state.get('logs', []),
        "user_xp": st.session_state.get('user_xp', 0),
        "user_lvl": st.session_state.get('user_lvl', 1),
        "game_mode": st.session_state.get('game_mode', "Séide"),
        "current_date": st.session_state.get('current_date', datetime.today().strftime("%Y-%m-%d"))
    }
    
    try:
        # Upsert: met à jour si user_id existe, sinon crée
        supabase.table(TABLE_NAME).upsert({
            "user_id": USER_ID,
            "data": payload
        }).execute()
    except Exception as e:
        st.error(f"Erreur sauvegarde DB: {e}")


# --- INITIALISATION SESSION STATE ---
if 'data_loaded' not in st.session_state:
    # Valeurs par défaut (écrasées si DB répond)
    st.session_state.tasks = []
    st.session_state.logs = []
    st.session_state.user_xp = 0
    st.session_state.user_lvl = 1
    st.session_state.game_mode = "Séide"
    st.session_state.current_date = datetime.today().strftime("%Y-%m-%d")
    
    # Tentative de chargement DB au lancement
    load_data_from_db()
    st.session_state.data_loaded = True

# --- CONSTANTES ---
FIXED_TASK_XP = 20 

# --- FONCTIONS LOGIQUES ---

def get_current_rank_info():
    lvl = st.session_state.user_lvl
    current_title = "Inconnu"
    current_color = "#000000"
    for t_lvl, t_name, t_color in TITLES:
        if lvl >= t_lvl:
            current_title = t_name
            current_color = t_color
        else:
            break
    return current_title, current_color

def get_max_slots():
    return 5 + (st.session_state.user_lvl // 10)

def get_tasks():
    return st.session_state.tasks

def add_task(name):
    if len(st.session_state.tasks) >= get_max_slots():
        return False, "Nombre maximum de slots atteint pour votre niveau !"
    
    new_id = len(st.session_state.tasks) + 1 
    if st.session_state.tasks:
        new_id = max([t['id'] for t in st.session_state.tasks]) + 1
        
    st.session_state.tasks.append({"id": new_id, "name": name})
    save_data_to_db() # SAVE
    return True, "Tâche ajoutée."

def delete_task(task_id):
    st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task_id]
    save_data_to_db() # SAVE

def get_daily_log(date):
    for log in st.session_state.logs:
        if log['date'] == date:
            return log
    return None

def validate_task(task_id, date):
    log = get_daily_log(date)
    if not log:
        log = {
            "date": date, 
            "tasks_completed": [], 
            "level_up": False,
            "xp_snapshot": st.session_state.user_xp 
        }
        st.session_state.logs.append(log)
    
    if task_id not in log['tasks_completed']:
        log['tasks_completed'].append(task_id)
        st.session_state.user_xp += FIXED_TASK_XP
        log['xp_snapshot'] = st.session_state.user_xp 
        check_levelup(date)
        save_data_to_db() # SAVE

def check_levelup(date):
    required_xp = st.session_state.user_lvl * 100
    if st.session_state.user_xp >= required_xp:
        st.session_state.user_lvl += 1
        st.session_state.user_xp -= required_xp 
        log = get_daily_log(date)
        if log: log['level_up'] = True
        st.balloons()

def apply_exalte_penalty(log_entry):
    if st.session_state.game_mode == "Exalté":
        total_tasks = len(st.session_state.tasks)
        completed = len(log_entry['tasks_completed'])
        
        if total_tasks > 0 and completed < total_tasks:
            missed = total_tasks - completed
            penalty = missed * FIXED_TASK_XP
            
            st.session_state.user_xp -= penalty
            if st.session_state.user_xp < 0:
                if st.session_state.user_lvl > 1:
                    st.session_state.user_lvl -= 1
                    st.session_state.user_xp = (st.session_state.user_lvl * 100) + st.session_state.user_xp
                else:
                    st.session_state.user_xp = 0

def skip_day():
    current_log = get_daily_log(st.session_state.current_date)
    if not current_log:
        current_log = {
            "date": st.session_state.current_date, 
            "tasks_completed": [], 
            "level_up": False,
            "xp_snapshot": st.session_state.user_xp
        }
        st.session_state.logs.append(current_log)
    
    apply_exalte_penalty(current_log)
    current_log['xp_snapshot'] = st.session_state.user_xp

    curr = datetime.strptime(st.session_state.current_date, "%Y-%m-%d")
    st.session_state.current_date = (curr + timedelta(days=1)).strftime("%Y-%m-%d")
    save_data_to_db() # SAVE

# --- UI LAYOUT ---

# 1. EN-TÊTE
title_name, title_color = get_current_rank_info()
st.markdown(f"<h3 style='text-align: center; color: {title_color};'>Niveau {st.session_state.user_lvl} - {title_name}</h3>", unsafe_allow_html=True)

xp_needed = st.session_state.user_lvl * 100
progress_val = min(st.session_state.user_xp / xp_needed, 1.0)
st.progress(progress_val)
st.caption(f"XP: {st.session_state.user_xp} / {xp_needed}")

# 2. TABS
tabs = st.tabs(["📜 Quête", "🛠 Config", "📈 Progression"])

# --- TAB QUÊTE ---
with tabs[0]:
    st.subheader(f"Journal du {st.session_state.current_date}")
    
    tasks = get_tasks()
    log = get_daily_log(st.session_state.current_date)
    completed_ids = log['tasks_completed'] if log else []
    
    if not tasks:
        st.info("Aucune tâche active. Configurez vos slots.")
    
    for task in tasks:
        col_name, col_btn = st.columns([0.7, 0.3])
        is_done = task['id'] in completed_ids
        
        with col_name:
            if is_done:
                st.markdown(f"~~**{task['name']}**~~")
            else:
                st.markdown(f"**{task['name']}**")
                
        with col_btn:
            if is_done:
                st.success("Validé")
            else:
                if st.button("Valider", key=f"val_{task['id']}"):
                    validate_task(task['id'], st.session_state.current_date)
                    st.rerun()

# --- TAB CONFIG ---
with tabs[1]:
    st.header("Configuration")
    
    st.subheader("Mode de Jeu")
    current_mode_index = 0 if st.session_state.game_mode == "Séide" else 1
    new_mode = st.radio(
        "Choisissez votre difficulté :", 
        ["Séide", "Exalté"], 
        index=current_mode_index,
        help="Séide: Pas de perte d'XP. Exalté: Perte d'XP si tâches non faites."
    )
    if new_mode != st.session_state.game_mode:
        st.session_state.game_mode = new_mode
        save_data_to_db() # SAVE
        st.success(f"Mode changé en {new_mode}")

    st.divider()

    st.subheader(f"Slots de Tâches ({len(st.session_state.tasks)}/{get_max_slots()})")
    
    with st.form("add_task_form", clear_on_submit=True):
        col_in, col_sub = st.columns([0.7, 0.3])
        with col_in:
            new_task_name = st.text_input("Nouvelle tâche", placeholder="Ex: Faire 50 pompes")
        with col_sub:
            submitted = st.form_submit_button("Ajouter")
            
        if submitted and new_task_name:
            success, msg = add_task(new_task_name)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    
    if st.session_state.tasks:
        for task in st.session_state.tasks:
            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
            with c1:
                st.write(f"- {task['name']}")
            with c2:
                pass 
            with c3:
                if st.button("🗑️", key=f"del_{task['id']}"):
                    delete_task(task['id'])
                    st.rerun()
    
    st.divider()
    
    with st.expander("Voir les Rangs & Titres"):
        for t_lvl, t_name, t_color in TITLES:
            if st.session_state.user_lvl >= t_lvl:
                st.markdown(f"<span style='color:{t_color}'><b>Lvl {t_lvl} : {t_name}</b></span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:#ccc'>Lvl {t_lvl} : ???</span>", unsafe_allow_html=True)

    st.divider()
    
    with st.expander("Dev Tools"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sauter un jour (Skip + Penalty Check)"):
                skip_day()
                st.rerun()
        with c2:
            if st.button("HARD RESET DB", type="primary"):
                st.session_state.tasks = []
                st.session_state.logs = []
                st.session_state.user_xp = 0
                st.session_state.user_lvl = 1
                save_data_to_db()
                st.rerun()

# --- TAB PROGRESSION ---
with tabs[2]:
    st.header("Graphique")
    
    df_logs = pd.DataFrame(st.session_state.logs)
    
    if not df_logs.empty:
        df_logs['date_dt'] = pd.to_datetime(df_logs['date'])
        df_logs = df_logs.sort_values('date_dt')
        
        current_total_tasks = max(len(st.session_state.tasks), 1)
        
        def get_status_color(row):
            count = len(row['tasks_completed'])
            if count == 0: return 'red'
            if count >= current_total_tasks: return 'green'
            return 'orange'
            
        df_logs['color'] = df_logs.apply(get_status_color, axis=1)

        st.caption("Filtres du graphique :")
        col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns(5)
        
        show_curve = col_l1.checkbox("🟦 Courbe", True)
        show_100 = col_l2.checkbox("🟢 Tâches réalisées", True)
        show_mid = col_l3.checkbox("🟠 Tâches partielles", True)
        show_0 = col_l4.checkbox("🔴 Aucune tâche", True)
        show_lvlup = col_l5.checkbox("⚫ Lvl Up !", True)

        with plt.xkcd():
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if show_curve:
                ax.plot(df_logs['date_dt'], df_logs['xp_snapshot'], color='blue', alpha=0.5, linewidth=2)
            
            for _, row in df_logs.iterrows():
                date_val = row['date_dt']
                xp_val = row['xp_snapshot']
                color = row['color']
                is_lvl_up = row['level_up']
                
                if is_lvl_up and show_lvlup:
                     ax.scatter([date_val], [xp_val], color='black', s=200, marker='*', zorder=10)
                
                if color == 'green' and show_100:
                    ax.scatter([date_val], [xp_val], color='green', s=100, zorder=5)
                elif color == 'orange' and show_mid:
                    ax.scatter([date_val], [xp_val], color='orange', s=100, zorder=5)
                elif color == 'red' and show_0:
                    ax.scatter([date_val], [xp_val], color='red', s=100, zorder=5)

            ax.set_ylabel("XP Totale")
            ax.set_xlabel("Date")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            fig.autofmt_xdate()
            fig.patch.set_alpha(0)
            ax.patch.set_alpha(0)
            
            st.pyplot(fig)
            
    else:
        st.info("Synchronisation DB... ou aucune donnée disponible.")

# --- DEPENDANCES (requirements.txt) ---
# streamlit
# pandas
# matplotlib
# supabase
