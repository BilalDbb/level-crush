import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta

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
    /* Masquer le menu hamburger standard pour faire plus "App" */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION SESSION STATE ---
if 'tasks' not in st.session_state:
    # Structure: id, name (XP et Mode sont gérés globalement/fixe maintenant)
    st.session_state.tasks = []

if 'logs' not in st.session_state:
    # Structure: date (str), tasks_completed (list of ids), xp_at_end_of_day (int), status (100, partial, 0)
    st.session_state.logs = []

if 'user_xp' not in st.session_state:
    st.session_state.user_xp = 0

if 'user_lvl' not in st.session_state:
    st.session_state.user_lvl = 1

if 'game_mode' not in st.session_state:
    st.session_state.game_mode = "Séide" # Default

if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.today().strftime("%Y-%m-%d")

# --- CONSTANTES ---
FIXED_TASK_XP = 20 # Valeur fixe par défaut pour l'instant

# --- FONCTIONS LOGIQUES ---

def get_current_rank_info():
    lvl = st.session_state.user_lvl
    current_title = "Inconnu"
    current_color = "#000000"
    
    # On parcourt la liste pour trouver le titre actif le plus élevé
    for t_lvl, t_name, t_color in TITLES:
        if lvl >= t_lvl:
            current_title = t_name
            current_color = t_color
        else:
            break
    return current_title, current_color

def get_max_slots():
    # 5 slots au niveau 1 + 1 slot tous les 10 niveaux
    return 5 + (st.session_state.user_lvl // 10)

def get_tasks():
    return st.session_state.tasks

def add_task(name):
    if len(st.session_state.tasks) >= get_max_slots():
        return False, "Nombre maximum de slots atteint pour votre niveau !"
    
    new_id = len(st.session_state.tasks) + 1 # Simple ID generation
    # En cas de suppression, l'ID peut être dupliqué avec cette méthode simple, 
    # mais suffisant pour la démo sans BDD réelle.
    if st.session_state.tasks:
        new_id = max([t['id'] for t in st.session_state.tasks]) + 1
        
    st.session_state.tasks.append({"id": new_id, "name": name})
    return True, "Tâche ajoutée."

def delete_task(task_id):
    st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task_id]

def update_task(task_id, new_name):
    for t in st.session_state.tasks:
        if t['id'] == task_id:
            t['name'] = new_name

def get_daily_log(date):
    for log in st.session_state.logs:
        if log['date'] == date:
            return log
    return None

def validate_task(task_id, date):
    log = get_daily_log(date)
    if not log:
        # Création du log du jour s'il n'existe pas
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
        log['xp_snapshot'] = st.session_state.user_xp # Update snapshot
        check_levelup(date)

def check_levelup(date):
    required_xp = st.session_state.user_lvl * 100
    if st.session_state.user_xp >= required_xp:
        st.session_state.user_lvl += 1
        st.session_state.user_xp -= required_xp # Reset barre XP (keep surplus)
        
        # Log le level up
        log = get_daily_log(date)
        if log: log['level_up'] = True
        st.balloons()

def apply_exalte_penalty(log_entry):
    """
    Applique la pénalité si le mode est Exalté et que la journée est passée/validée
    sans 100% de réussite.
    """
    if st.session_state.game_mode == "Exalté":
        total_tasks = len(st.session_state.tasks)
        completed = len(log_entry['tasks_completed'])
        
        if total_tasks > 0 and completed < total_tasks:
            missed = total_tasks - completed
            penalty = missed * FIXED_TASK_XP
            
            st.session_state.user_xp -= penalty
            # Gestion de la descente de niveau
            if st.session_state.user_xp < 0:
                if st.session_state.user_lvl > 1:
                    st.session_state.user_lvl -= 1
                    # On remet l'XP au max du niveau précédent moins la dette
                    st.session_state.user_xp = (st.session_state.user_lvl * 100) + st.session_state.user_xp
                else:
                    st.session_state.user_xp = 0 # Pas de niveau 0

def skip_day():
    """Simule le passage au jour suivant et applique les règles de fin de journée"""
    current_log = get_daily_log(st.session_state.current_date)
    
    # Si pas de log pour aujourd'hui, on en crée un vide pour marquer l'échec (0 tâches)
    if not current_log:
        current_log = {
            "date": st.session_state.current_date, 
            "tasks_completed": [], 
            "level_up": False,
            "xp_snapshot": st.session_state.user_xp
        }
        st.session_state.logs.append(current_log)
    
    # Appliquer pénalité Exalté sur la journée qui se termine
    apply_exalte_penalty(current_log)
    
    # Mettre à jour le snapshot XP final après pénalité
    current_log['xp_snapshot'] = st.session_state.user_xp

    # Avancer la date
    curr = datetime.strptime(st.session_state.current_date, "%Y-%m-%d")
    st.session_state.current_date = (curr + timedelta(days=1)).strftime("%Y-%m-%d")


# --- UI LAYOUT ---

# 1. EN-TÊTE (Rank & Progress)
title_name, title_color = get_current_rank_info()
st.markdown(f"<h3 style='text-align: center; color: {title_color};'>Niveau {st.session_state.user_lvl} - {title_name}</h3>", unsafe_allow_html=True)

# Barre de progression XP
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
        # Container style card
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
    
    # Choix du mode global
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
        st.success(f"Mode changé en {new_mode}")

    st.divider()

    # Gestion des tâches
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
    
    # Liste tâches existantes
    if st.session_state.tasks:
        for task in st.session_state.tasks:
            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
            with c1:
                st.write(f"- {task['name']}")
            with c2:
                # Edition simple via popover ou expander serait mieux mais on reste simple
                pass 
            with c3:
                if st.button("🗑️", key=f"del_{task['id']}"):
                    delete_task(task['id'])
                    st.rerun()
    
    st.divider()
    
    # Affichage des Rangs
    with st.expander("Voir les Rangs & Titres"):
        for t_lvl, t_name, t_color in TITLES:
            if st.session_state.user_lvl >= t_lvl:
                st.markdown(f"<span style='color:{t_color}'><b>Lvl {t_lvl} : {t_name}</b></span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:#ccc'>Lvl {t_lvl} : ???</span>", unsafe_allow_html=True)

    st.divider()
    
    # Dev Tools
    with st.expander("Dev Tools"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sauter un jour (Skip + Penalty Check)"):
                skip_day()
                st.rerun()
        with c2:
            if st.button("HARD RESET", type="primary"):
                st.session_state.clear()
                st.rerun()

# --- TAB PROGRESSION ---
with tabs[2]:
    st.header("Graphique")
    
    df_logs = pd.DataFrame(st.session_state.logs)
    
    if not df_logs.empty:
        df_logs['date_dt'] = pd.to_datetime(df_logs['date'])
        df_logs = df_logs.sort_values('date_dt')
        
        # Calcul du % pour déterminer la couleur du point
        # Attention: pour l'historique, il faudrait stocker le nb de taches ce jour là.
        # Ici on approxime avec le nb actuel de taches.
        current_total_tasks = max(len(st.session_state.tasks), 1)
        
        def get_status_color(row):
            count = len(row['tasks_completed'])
            if count == 0: return 'red'
            if count >= current_total_tasks: return 'green'
            return 'orange'
            
        df_logs['color'] = df_logs.apply(get_status_color, axis=1)

        # -- Interactive Legend (Streamlit widgets) --
        st.caption("Filtres du graphique :")
        col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns(5)
        
        show_curve = col_l1.checkbox("🟦 Courbe", True)
        show_100 = col_l2.checkbox("🟢 Tâches réalisées", True)
        show_mid = col_l3.checkbox("🟠 Tâches partielles", True)
        show_0 = col_l4.checkbox("🔴 Aucune tâche", True)
        show_lvlup = col_l5.checkbox("⚫ Lvl Up !", True)

        # -- Matplotlib Plot --
        with plt.xkcd():
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 1. Courbe XP (Bleue)
            if show_curve:
                ax.plot(df_logs['date_dt'], df_logs['xp_snapshot'], color='blue', alpha=0.5, linewidth=2)
            
            # 2. Points de status
            for _, row in df_logs.iterrows():
                date_val = row['date_dt']
                xp_val = row['xp_snapshot']
                color = row['color']
                is_lvl_up = row['level_up']
                
                # Level Up Marker
                if is_lvl_up and show_lvlup:
                     ax.scatter([date_val], [xp_val], color='black', s=200, marker='*', zorder=10)
                
                # Daily Status Marker
                if color == 'green' and show_100:
                    ax.scatter([date_val], [xp_val], color='green', s=100, zorder=5)
                elif color == 'orange' and show_mid:
                    ax.scatter([date_val], [xp_val], color='orange', s=100, zorder=5)
                elif color == 'red' and show_0:
                    ax.scatter([date_val], [xp_val], color='red', s=100, zorder=5)

            ax.set_ylabel("XP Totale")
            ax.set_xlabel("Date")
            
            # Retrait du cadre supérieur et droit pour faire plus "clean"
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            fig.autofmt_xdate()
            fig.patch.set_alpha(0)
            ax.patch.set_alpha(0)
            
            st.pyplot(fig)
            
    else:
        st.info("Aucune donnée disponible. Validez des tâches ou sautez un jour pour voir le graphique.")

# --- DEPENDANCES ---
# streamlit
# pandas
# matplotlib
