import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from supabase import create_client, Client

# --- 1. CONFIGURATION & CONNEXION SUPABASE ---
st.set_page_config(page_title="RPG Gestion", layout="centered")

# Fonction pour initialiser la connexion (mise en cache pour la perf)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Erreur de connexion Supabase : {e}")
    st.stop()

# --- 2. CSS & STYLES (CORRECTIFS VISUELS) ---
def inject_custom_css():
    st.markdown("""
    <style>
    /* === DESIGN DES QUÊTES (Style Carte Propre) === */
    .quest-item {
        background-color: #ffffff;
        border-left: 6px solid #4a90e2; /* Bordure bleue */
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        font-size: 16px;
        font-weight: 500;
        color: #333333;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: transform 0.2s ease-in-out;
    }
    .quest-item:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* === CORRECTIFS THÈME SOMBRE (DARK MODE) === */
    @media (prefers-color-scheme: dark) {
        .quest-item {
            background-color: #262730; /* Gris foncé Streamlit */
            color: #ffffff !important;
            border-left: 6px solid #ffbd45; /* Orange contrasté */
            border: 1px solid rgba(255,255,255,0.1);
        }
        /* Journal de bord (Accordéon) - Force le texte blanc */
        .streamlit-expanderHeader {
            color: #ffffff !important;
            background-color: #262730 !important;
        }
        .streamlit-expanderContent p {
            color: #e0e0e0 !important;
        }
        /* Boutons visibles */
        button {
            border-color: rgba(255,255,255,0.2) !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. GESTION DES DONNÉES (CRUD SUPABASE) ---

def get_taches():
    """Récupère les tâches depuis Supabase"""
    response = supabase.table("taches").select("*").execute()
    return response.data

def add_tache(nom, xp):
    """Ajoute une tâche dans Supabase"""
    # Pas besoin d'envoyer l'ID si ta colonne ID est en auto-increment (serial/identity)
    data = {"nom": nom, "xp": xp, "created_at": str(datetime.datetime.now())}
    supabase.table("taches").insert(data).execute()

def delete_tache(tache_id):
    """Supprime une tâche via son ID"""
    supabase.table("taches").delete().eq("id", tache_id).execute()

def add_log(message):
    """Ajoute une entrée dans le journal"""
    data = {"date": str(datetime.date.today()), "message": message}
    supabase.table("journal").insert(data).execute()

def get_journal():
    """Récupère l'historique"""
    response = supabase.table("journal").select("*").order("date", desc=True).execute()
    return response.data

# --- 4. INTERFACE PRINCIPALE ---
st.title("🛡️ Tableau de Bord RPG")

# Navigation
tab1, tab2, tab3 = st.tabs(["📜 Quêtes", "⚙️ Config", "📊 Stats & Journal"])

# === ONGLET 1 : QUÊTES ===
with tab1:
    st.subheader("Quêtes actives")
    
    # Chargement des données
    taches = get_taches()
    
    if not taches:
        st.info("Aucune quête en cours. Va dans Config pour en ajouter !")
    
    for tache in taches:
        col_visuel, col_action = st.columns([5, 1])
        
        with col_visuel:
            st.markdown(f"""
            <div class="quest-item">
                <span>{tache['nom']}</span>
                <span style="font-size:0.8em; opacity:0.7;">+{tache['xp']} XP</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col_action:
            st.write("") 
            # Utilisation de l'ID unique de la base de données pour la clé
            if st.button("✅", key=f"btn_{tache['id']}", help="Valider la quête"):
                add_log(f"Quête '{tache['nom']}' terminée (+{tache['xp']} XP).")
                delete_tache(tache['id'])
                st.rerun()

# === ONGLET 2 : CONFIGURATION ===
with tab2:
    st.subheader("Ajouter une nouvelle quête")
    
    c_input, c_btn = st.columns([4, 1])
    
    with c_input:
        new_task = st.text_input("Nom de la tâche", placeholder="Ex: Méditer 10 min", label_visibility="collapsed")
        
    with c_btn:
        btn_add = st.button("Ajouter", use_container_width=True)

    if btn_add:
        if new_task:
            add_tache(new_task, 10) # 10 XP par défaut
            st.success(f"Quête '{new_task}' sauvegardée !")
            st.rerun()
        else:
            st.warning("Écris un nom de tâche d'abord.")

# === ONGLET 3 : STATS & JOURNAL ===
with tab3:
    st.subheader("Journal de bord")
    
    logs = get_journal()
    
    with st.expander("📖 Voir l'historique (Journal)", expanded=False):
        if logs:
            for log in logs:
                st.write(f"- **{log['date']}**: {log['message']}")
        else:
            st.write("Le journal est vide.")

    st.divider()
    
    st.subheader("Statistiques")
    
    # Données fictives (à connecter à Supabase si tu as une table 'stats')
    data = {'Force': 20, 'Intel': 35, 'Endu': 15, 'Charisme': 10}
    names = list(data.keys())
    values = list(data.values())

    # Config Matplotlib "Thème-Proof"
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)
    
    ax.bar(names, values, color='#4a90e2')
    
    TEXT_COLOR = '#909090' 
    ax.tick_params(colors=TEXT_COLOR, which='both')
    for spine in ax.spines.values():
        spine.set_edgecolor(TEXT_COLOR)
        
    ax.set_title("Répartition des Stats", color=TEXT_COLOR)
    
    st.pyplot(fig)
