import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONFIGURATION SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    DB_CONNECTED = True
except Exception as e:
    DB_CONNECTED = False
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

# --- STYLE CSS (POLICE MANUSCRITE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap');

    html, body, [class*="css"] {
        font-family: 'Patrick Hand', cursive;
    }
    
    p, label, .stMarkdown {
        font-size: 1.1rem !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        font-family: 'Patrick Hand', cursive; 
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
            data = response.data[0]['data']
            st.session_state.tasks = data.get('tasks', [])
            st.session_state.logs = data.get('logs', [])
            st.session_state.user_xp = data.get('user_xp', 0)
            st.session_state.user_lvl = data.get('user_lvl', 1)
            st.session_state.game_mode = data.get('game_mode', "Séide")
            st.session_state.current_date = data.get('current_date', datetime.today().strftime("%Y-%m-%d"))
        else:
            save_data_to_db() 
            
    except Exception as e:
        st.error(f"Erreur chargement DB: {e}")

def save_data_to_db():
    """Sauvegarde tout l'état actuel dans la colonne JSONB"""
    if not DB_CONNECTED: return

    payload = {
        "tasks": st.session_state.get('tasks', []),
        "logs": st.session_state.get('logs', []),
        "user_xp": st.session_state.get('user_xp', 0),
        "user_lvl": st.session_state.get('user_lvl', 1),
        "game_mode": st.session_state.get('game_mode', "Séide"),
        "current_date": st.session_state.get('current_date', datetime.today().strftime("%Y-%m-%d"))
    }
    
    try:
        supabase.table(TABLE_NAME).upsert({
            "user_id": USER_ID,
            "data": payload
        }).execute()
    except Exception as e:
        st.error(f"Erreur sauvegarde DB: {e}")


# --- INITIALISATION SESSION STATE ---
if 'data_loaded' not in st.session_state:
    st.session_state.tasks = []
    st.session_state.logs = []
    st.session_state.user_xp = 0
    st.session_state.user_lvl = 1
    st.session_state.game_mode = "Séide"
    st.session_state.current_date = datetime.today().strftime("%Y-%m-%d")
    
    load_data_from_db()
    st.session_state.data_loaded = True

# --- CONSTANTES & LOGIQUE XP ---
FIXED_TASK_XP = 229

def get_level_cost(level):
    """
    Calcule le coût en XP pour compléter le niveau 'level' (passer de level à level+1).
    Formule: Coeff * (niveau^1.2)
    """
    exponent = 1.2
    coeff = 30
    
    if level <= 5:
        coeff = 150
    elif 6 <= level <= 10:
        coeff = 80
    
    return coeff * (level ** exponent)

def get_total_xp_required(target_level):
    """
    Calcule l'XP TOTAL cumulé requis pour atteindre le 'target_level'.
    """
    if target_level == 1:
        return 0
    
    # Règle spéciale lvl 100
    if target_level == 100:
        return get_total_xp_required(99) * 2
        
    total = 0
    # On somme les coûts de tous les niveaux précédents
    for lvl in range(1, target_level):
        total += get_level_cost(lvl)
        
    return total

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
    save_data_to_db() 
    return True, "Tâche ajoutée."

def delete_task(task_id):
    st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task_id]
    save_data_to_db()

def get_daily_log(date):
    for log in st.session_state.logs:
        if log['date'] == date:
            return log
    return None

def check_levelup(date):
    """Vérifie si l'XP totale permet de monter de niveau."""
    current_lvl = st.session_state.user_lvl
    # On boucle au cas où on gagne plusieurs niveaux d'un coup
    while True:
        xp_needed_next = get_total_xp_required(current_lvl + 1)
        if st.session_state.user_xp >= xp_needed_next:
            current_lvl += 1
            # Pas de ballons
        else:
            break
            
    if current_lvl > st.session_state.user_lvl:
        st.session_state.user_lvl = current_lvl
        log = get_daily_log(date)
        if log: log['level_up'] = True

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
        # Gain XP cumulative
        st.session_state.user_xp += FIXED_TASK_XP
        log['xp_snapshot'] = st.session_state.user_xp 
        check_levelup(date)
        save_data_to_db()

def apply_exalte_penalty(log_entry):
    """
    En mode Exalté, retire l'XP équivalent au gain pour chaque tâche ratée.
    """
    if st.session_state.game_mode == "Exalté":
        total_tasks = len(st.session_state.tasks)
        completed = len(log_entry['tasks_completed'])
        
        if total_tasks > 0 and completed < total_tasks:
            missed = total_tasks - completed
            penalty = missed * FIXED_TASK_XP
            
            st.session_state.user_xp -= penalty
            if st.session_state.user_xp < 0:
                st.session_state.user_xp = 0
            
            # Gestion de la perte de niveau (Level Down)
            # Si l'XP passe sous le seuil du niveau actuel
            while st.session_state.user_lvl > 1:
                threshold_current = get_total_xp_required(st.session_state.user_lvl)
                if st.session_state.user_xp < threshold_current:
                    st.session_state.user_lvl -= 1
                else:
                    break

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
    save_data_to_db()

# --- UI LAYOUT ---

# 1. EN-TÊTE
title_name, title_color = get_current_rank_info()
st.markdown(f"<h3 style='text-align: center; color: {title_color}; font-family: Patrick Hand, cursive;'>Niveau {st.session_state.user_lvl} - {title_name}</h3>", unsafe_allow_html=True)

# Barre de progression (Calculée relative au niveau en cours)
current_level_floor = get_total_xp_required(st.session_state.user_lvl)
next_level_ceiling = get_total_xp_required(st.session_state.user_lvl + 1)
xp_in_level = st.session_state.user_xp - current_level_floor
xp_needed_for_level = next_level_ceiling - current_level_floor

if xp_needed_for_level > 0:
    progress_val = min(max(xp_in_level / xp_needed_for_level, 0.0), 1.0)
else:
    progress_val = 1.0

st.progress(progress_val)
st.caption(f"XP: {int(st.session_state.user_xp)} / {int(next_level_ceiling)} (Total)")

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

    st.divider()

    # --- DEV TOOLS ---
    with st.expander("👨‍💻 Dev Tools (Test Zone)"):
        st.warning("Zone développeur")
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
        save_data_to_db() 
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
