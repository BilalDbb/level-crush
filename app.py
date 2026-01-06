import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Task RPG", page_icon="⚔️")

# --- STYLE CSS (Optionnel pour le look) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION SESSION STATE (Simulation BDD) ---
if 'tasks' not in st.session_state:
    # Structure: id, name, xp_reward, mode (seide/exalte)
    st.session_state.tasks = [
        {"id": 1, "name": "Boire 2L d'eau", "xp": 10, "mode": "Séide"},
        {"id": 2, "name": "Code 1h", "xp": 50, "mode": "Exalté"}
    ]

if 'logs' not in st.session_state:
    # Structure: date (str), tasks_completed (list of ids), level_up (bool)
    # On génère un peu d'historique pour tester le graphique
    st.session_state.logs = []
    base = datetime.today()
    for x in range(7, 0, -1):
        date = (base - timedelta(days=x)).strftime("%Y-%m-%d")
        st.session_state.logs.append({
            "date": date,
            "tasks_completed": [1, 2] if random.random() > 0.5 else [1], # Random completion
            "level_up": True if x == 4 else False # Fake level up
        })

if 'user_xp' not in st.session_state:
    st.session_state.user_xp = 120

if 'user_lvl' not in st.session_state:
    st.session_state.user_lvl = 2

if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.today().strftime("%Y-%m-%d")

# --- FONCTIONS ---

def get_tasks():
    return st.session_state.tasks

def add_task(name, xp, mode):
    new_id = len(st.session_state.tasks) + 1
    st.session_state.tasks.append({"id": new_id, "name": name, "xp": xp, "mode": mode})

def delete_task(task_id):
    st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task_id]

def update_task(task_id, new_name, new_xp, new_mode):
    for t in st.session_state.tasks:
        if t['id'] == task_id:
            t['name'] = new_name
            t['xp'] = new_xp
            t['mode'] = new_mode

def get_daily_log(date):
    for log in st.session_state.logs:
        if log['date'] == date:
            return log
    return None

def toggle_task_completion(task_id, date):
    log = get_daily_log(date)
    if not log:
        log = {"date": date, "tasks_completed": [], "level_up": False}
        st.session_state.logs.append(log)
    
    if task_id in log['tasks_completed']:
        log['tasks_completed'].remove(task_id)
        # Retirer XP (simplifié)
        task = next((t for t in st.session_state.tasks if t['id'] == task_id), None)
        if task: st.session_state.user_xp -= task['xp']
    else:
        log['tasks_completed'].append(task_id)
        # Ajouter XP
        task = next((t for t in st.session_state.tasks if t['id'] == task_id), None)
        if task: st.session_state.user_xp += task['xp']

def check_levelup():
    # Seuil arbitraire : lvl * 100 XP
    required_xp = st.session_state.user_lvl * 100
    if st.session_state.user_xp >= required_xp:
        st.session_state.user_lvl += 1
        st.session_state.user_xp -= required_xp
        # Marquer le level up dans le log d'aujourd'hui
        log = get_daily_log(st.session_state.current_date)
        if log:
            log['level_up'] = True
        st.balloons()
        return True
    return False

# --- UI ---

tabs = st.tabs(["📜 Quête", "🛠 Config", "📈 Progression"])

# --- TAB 1: QUÊTE ---
with tabs[0]:
    st.header(f"Quêtes du {st.session_state.current_date}")
    
    tasks = get_tasks()
    log = get_daily_log(st.session_state.current_date)
    completed_ids = log['tasks_completed'] if log else []
    
    if not tasks:
        st.info("Aucune tâche configurée. Va dans l'onglet Config.")
    
    for task in tasks:
        col1, col2 = st.columns([0.1, 0.9])
        is_checked = task['id'] in completed_ids
        
        with col1:
            if st.checkbox("", value=is_checked, key=f"check_{task['id']}"):
                if not is_checked:
                    toggle_task_completion(task['id'], st.session_state.current_date)
                    check_levelup()
                    st.rerun()
            else:
                if is_checked:
                    toggle_task_completion(task['id'], st.session_state.current_date)
                    st.rerun()
        
        with col2:
            st.write(f"**{task['name']}** ({task['xp']} XP) - *{task['mode']}*")

# --- TAB 2: CONFIG ---
with tabs[1]:
    st.header("Configuration des Tâches")
    
    # Formulaire d'ajout
    with st.form("add_task_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 1, 2])
        with c1:
            new_name = st.text_input("Nom de la tâche")
        with c2:
            new_xp = st.number_input("XP", min_value=1, value=10)
        with c3:
            new_mode = st.selectbox("Mode", ["Séide", "Exalté"])
        submitted = st.form_submit_button("Ajouter")
        
        if submitted and new_name:
            add_task(new_name, new_xp, new_mode)
            st.success("Tâche ajoutée !")
            st.rerun()

    st.divider()
    
    # Liste des tâches existantes (Persistante !)
    st.subheader("Tâches existantes")
    for i, task in enumerate(st.session_state.tasks):
        with st.expander(f"{task['name']} ({task['xp']} XP)"):
            with st.form(key=f"edit_{task['id']}"):
                e_name = st.text_input("Nom", value=task['name'])
                e_xp = st.number_input("XP", value=task['xp'])
                e_mode = st.selectbox("Mode", ["Séide", "Exalté"], index=0 if task['mode']=="Séide" else 1)
                
                c_edit, c_del = st.columns(2)
                with c_edit:
                    if st.form_submit_button("Modifier"):
                        update_task(task['id'], e_name, e_xp, e_mode)
                        st.rerun()
                with c_del:
                    if st.form_submit_button("Supprimer", type="primary"):
                        delete_task(task['id'])
                        st.rerun()

    st.divider()
    
    # Dev Tools
    with st.expander("👨‍💻 Dev Tools (Test Zone)"):
        st.warning("Zone développeur")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sauter un jour (Skip Day)"):
                curr = datetime.strptime(st.session_state.current_date, "%Y-%m-%d")
                st.session_state.current_date = (curr + timedelta(days=1)).strftime("%Y-%m-%d")
                st.rerun()
        with c2:
            if st.button("HARD RESET", type="primary"):
                st.session_state.clear()
                st.rerun()

# --- TAB 3: PROGRESSION ---
with tabs[2]:
    st.header("Tableau de bord")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Niveau Actuel", st.session_state.user_lvl)
    with col2:
        st.metric("XP Totale", st.session_state.user_xp)

    st.subheader("Graphique de Progression")
    
    # Préparation des données pour le graph
    df_logs = pd.DataFrame(st.session_state.logs)
    if not df_logs.empty:
        df_logs['date_dt'] = pd.to_datetime(df_logs['date'])
        df_logs = df_logs.sort_values('date_dt')
        
        # Calcul du % de complétion par jour
        total_tasks_count = len(st.session_state.tasks) if st.session_state.tasks else 1
        # Note: Pour un historique précis, il faudrait stocker le nb de tâches total ce jour là. 
        # Ici on prend le nb actuel par simplification.
        
        df_logs['completion_pct'] = df_logs['tasks_completed'].apply(lambda x: len(x) / total_tasks_count * 100)
        
        # Filtres (Légende interactive simulée)
        st.caption("Filtres (Cliquez pour masquer/afficher)")
        c1, c2, c3, c4, c5 = st.columns(5)
        show_curve = c1.checkbox("Courbe", True)
        show_100 = c2.checkbox("100% (Vert)", True)
        show_mid = c3.checkbox("1-99% (Orange)", True)
        show_0 = c4.checkbox("0% (Rouge)", True)
        show_lvlup = c5.checkbox("Lvl Up (Noir)", True)

        # Création du graphique style "Fait main"
        with plt.xkcd():
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 1. La Courbe
            if show_curve:
                ax.plot(df_logs['date_dt'], df_logs['completion_pct'], color='blue', alpha=0.3, label='Progression')

            # 2. Les Points (Logique de couleur)
            for _, row in df_logs.iterrows():
                date_val = row['date_dt']
                pct = row['completion_pct']
                is_lvl_up = row['level_up']

                # Priorité au Level Up
                if is_lvl_up and show_lvlup:
                    ax.scatter([date_val], [pct], color='black', s=150, zorder=10, marker='D', label='Level Up')
                
                # Couleurs selon %
                if pct == 100 and show_100:
                    ax.scatter([date_val], [pct], color='green', s=100, zorder=5)
                elif pct == 0 and show_0:
                    ax.scatter([date_val], [pct], color='red', s=100, zorder=5)
                elif 0 < pct < 100 and show_mid:
                    ax.scatter([date_val], [pct], color='orange', s=100, zorder=5)

            ax.set_ylim(-5, 110)
            ax.set_ylabel("% Tâches accomplies")
            ax.set_title("Ma Super Progression")
            
            # Formatage des dates
            fig.autofmt_xdate()
            
            # Fond transparent pour le style
            fig.patch.set_alpha(0)
            ax.patch.set_alpha(0)
            
            st.pyplot(fig)
    else:
        st.write("Pas encore de données pour le graphique.")

# --- DEPENDANCES (requirements.txt) ---
# streamlit
# pandas
# matplotlib
