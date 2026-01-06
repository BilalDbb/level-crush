import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from supabase import create_client, Client

# --- 1. CONFIGURATION & CONNEXION SUPABASE ---
st.set_page_config(page_title="Level Crush", layout="centered")

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = init_connection()

# --- 2. CSS & STYLES (Mode sombre + Cartes + Alignement) ---
def inject_custom_css():
    st.markdown("""
    <style>
    /* === DESIGN DES QUÊTES (Style Carte Propre) === */
    .quest-item {
        background-color: #ffffff;
        border-left: 6px solid #4a90e2;
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
            background-color: #262730;
            color: #ffffff !important;
            border-left: 6px solid #ffbd45;
            border: 1px solid rgba(255,255,255,0.1);
        }
        /* Force le texte du journal (accordéon) en blanc */
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

# --- 3. FONCTIONS BDD ---

def get_taches():
    if not supabase: return []
    response = supabase.table("taches").select("*").order("id").execute()
    return response.data

def add_tache(nom, xp):
    if not supabase: return
    data = {"nom": nom, "xp": xp}
    supabase.table("taches").insert(data).execute()

def delete_tache(tache_id):
    if not supabase: return
    supabase.table("taches").delete().eq("id", tache_id).execute()

def add_log(message):
    if not supabase: return
    data = {"date": str(datetime.date.today()), "message": message}
    supabase.table("journal").insert(data).execute()

def get_journal():
    if not supabase: return []
    response = supabase.table("journal").select("*").order("date", desc=True).execute()
    return response.data

def reset_all_data():
    """Supprime toutes les données (Reset/Hard Restart)"""
    if not supabase: return
    # Suppression de toutes les lignes (attention: nécessite que la policy le permette)
    supabase.table("taches").delete().neq("id", 0).execute()
    supabase.table("journal").delete().neq("id", 0).execute()

# --- 4. INTERFACE PRINCIPALE ---
st.title("Level Crush")

if not supabase:
    st.error("Erreur de connexion Supabase. Vérifie tes secrets.")
    st.stop()

# RESTAURATION DES ONGLETS DEMANDÉS
tab_quetes, tab_progression, tab_config = st.tabs(["📜 Quêtes", "📈 Progression", "⚙️ Config"])

# === ONGLET 1 : QUÊTES ===
with tab_quetes:
    st.subheader("Quêtes actives")
    
    taches = get_taches()
    
    if not taches:
        st.info("Aucune quête en cours.")
    
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
            if st.button("✅", key=f"btn_{tache['id']}", help="Valider"):
                add_log(f"Quête '{tache['nom']}' terminée (+{tache['xp']} XP).")
                delete_tache(tache['id'])
                st.rerun()

# === ONGLET 2 : PROGRESSION (Restauré) ===
with tab_progression:
    st.subheader("Statistiques du héros")
    
    # Données fictives (à adapter si tu as une table stats)
    data = {'Force': 20, 'Intel': 35, 'Endu': 15, 'Charisme': 10}
    names = list(data.keys())
    values = list(data.values())

    # --- GRAPHIQUE MATPLOTLIB (Correction Mode Sombre + Légende) ---
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)
    
    bar_colors = ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f']
    ax.bar(names, values, color=bar_colors)
    
    # Couleur du texte adaptative (Gris clair lisible sur sombre et clair)
    TEXT_COLOR = '#A0A0A0' 
    ax.tick_params(colors=TEXT_COLOR, which='both')
    for spine in ax.spines.values():
        spine.set_edgecolor(TEXT_COLOR)
    
    ax.set_title("Répartition des attributs", color=TEXT_COLOR)
    
    # Légende manuelle pour être sûr qu'elle soit visible
    # On crée une légende fictive pour l'exemple
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=n) for c, n in zip(bar_colors, names)]
    
    # Correction visibilité légende
    leg = ax.legend(handles=legend_elements, loc='upper right', frameon=False)
    for text in leg.get_texts():
        text.set_color(TEXT_COLOR)

    st.pyplot(fig)

    st.divider()
    
    st.subheader("Journal de bord")
    logs = get_journal()
    
    # Le CSS 'dark-mode' s'applique ici pour la visibilité
    with st.expander("📖 Voir l'historique complet", expanded=False):
        if logs:
            for log in logs:
                st.write(f"- **{log['date']}**: {log['message']}")
        else:
            st.write("Le journal est vide.")

# === ONGLET 3 : CONFIGURATION (Boutons restaurés) ===
with tab_config:
    st.subheader("Ajouter une quête")
    
    # Alignement Input + Bouton Ajouter
    c_input, c_btn = st.columns([4, 1])
    with c_input:
        new_task = st.text_input("Nom de la tâche", placeholder="Ex: Méditer", label_visibility="collapsed")
    with c_btn:
        btn_add = st.button("Ajouter", use_container_width=True)

    if btn_add and new_task:
        add_tache(new_task, 10)
        st.success(f"Quête '{new_task}' sauvegardée !")
        st.rerun()

    st.divider()
    st.subheader("Gestion du temps & Reset")
    
    # RESTAURATION DES BOUTONS DE GESTION
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⏩ Sauter un jour", use_container_width=True):
            add_log("Journée sautée (Repos).")
            st.success("Jour passé !")
            st.rerun()
            
    with col2:
        if st.button("🔄 Reset", type="primary", use_container_width=True):
            reset_all_data()
            st.warning("Données réinitialisées.")
            st.rerun()
            
    with col3:
        if st.button("💀 Hard Restart", type="primary", use_container_width=True):
            reset_all_data()
            # Ici on pourrait ajouter une logique plus aggressive si besoin
            add_log("HARD RESTART EFFECTUÉ.")
            st.error("Système redémarré à zéro.")
            st.rerun()
