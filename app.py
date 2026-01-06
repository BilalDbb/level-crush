import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# Configuration de la page
st.set_page_config(page_title="RPG Gestion", layout="centered")

# --- 1. CSS & STYLES (CORRECTIFS VISUELS) ---
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
        /* Carte Quête en sombre */
        .quest-item {
            background-color: #262730; /* Gris foncé Streamlit */
            color: #ffffff !important;
            border-left: 6px solid #ffbd45; /* Orange pour le contraste */
            border: 1px solid rgba(255,255,255,0.1); /* Légère bordure globale */
        }
        
        /* Journal de bord (Accordéon) - Force le texte blanc */
        .streamlit-expanderHeader {
            color: #ffffff !important;
            background-color: #262730 !important;
        }
        .streamlit-expanderContent p {
            color: #e0e0e0 !important;
        }

        /* Boutons (pour qu'ils ne soient pas invisibles) */
        button {
            border-color: rgba(255,255,255,0.2) !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 2. GESTION DES DONNÉES (Session State) ---
if 'taches' not in st.session_state:
    st.session_state.taches = [
        {"nom": "Faire 30min de sport", "xp": 10, "id": 1},
        {"nom": "Lire 10 pages", "xp": 5, "id": 2}
    ]

if 'journal' not in st.session_state:
    st.session_state.journal = [
        "2023-10-25: Début de l'aventure.",
        "2023-10-26: Sport accompli avec succès."
    ]

# --- 3. INTERFACE PRINCIPALE ---
st.title("🛡️ Tableau de Bord RPG")

# Navigation par Onglets
tab1, tab2, tab3 = st.tabs(["📜 Quêtes", "⚙️ Config", "📊 Stats & Journal"])

# === ONGLET 1 : QUÊTES ===
with tab1:
    st.subheader("Quêtes actives")
    
    if not st.session_state.taches:
        st.info("Aucune quête en cours. Va dans Config pour en ajouter !")
    
    for tache in st.session_state.taches:
        # Affichage HTML propre avec le style CSS .quest-item défini plus haut
        # On utilise des colonnes pour mettre le bouton "Valider" (supprimer) à côté du visuel
        col_visuel, col_action = st.columns([5, 1])
        
        with col_visuel:
            st.markdown(f"""
            <div class="quest-item">
                <span>{tache['nom']}</span>
                <span style="font-size:0.8em; opacity:0.7;">+{tache['xp']} XP</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col_action:
            # Centrage vertical approximatif pour le bouton
            st.write("") 
            if st.button("✅", key=f"btn_{tache['id']}", help="Valider la quête"):
                st.session_state.taches.remove(tache)
                st.session_state.journal.append(f"{datetime.date.today()}: Quête '{tache['nom']}' terminée.")
                st.rerun()

# === ONGLET 2 : CONFIGURATION ===
with tab2:
    st.subheader("Ajouter une nouvelle quête")
    
    # CORRECTION ALIGNEMENT : Utilisation de st.columns([4, 1])
    # Le input prend 80% de la largeur, le bouton 20%
    c_input, c_btn = st.columns([4, 1])
    
    with c_input:
        new_task = st.text_input("Nom de la tâche", placeholder="Ex: Méditer 10 min", label_visibility="collapsed")
        
    with c_btn:
        # Pas de label, juste le bouton. L'alignement se fait via les colonnes.
        btn_add = st.button("Ajouter", use_container_width=True)

    if btn_add:
        if new_task:
            nouvelle_id = len(st.session_state.taches) + 100 # ID simple
            st.session_state.taches.append({"nom": new_task, "xp": 10, "id": nouvelle_id})
            st.success(f"Quête '{new_task}' ajoutée !")
            st.rerun()
        else:
            st.warning("Écris un nom de tâche d'abord.")

# === ONGLET 3 : STATS & JOURNAL ===
with tab3:
    st.subheader("Journal de bord")
    
    # Le CSS plus haut force la couleur du texte en blanc pour le mode sombre ici
    with st.expander("📖 Voir l'historique (Journal)", expanded=False):
        for log in st.session_state.journal:
            st.write(f"- {log}")

    st.divider()
    
    st.subheader("Statistiques")
    
    # Exemple de graphique Matplotlib avec correction pour le mode sombre
    # (Si tu utilises st.bar_chart, c'est automatique, mais voici pour Matplotlib)
    
    data = {'Force': 20, 'Intel': 35, 'Endu': 15, 'Charisme': 10}
    names = list(data.keys())
    values = list(data.values())

    # Détection basique du thème (optionnel, ou forcer style sombre si besoin)
    # L'astuce ici est de configurer les couleurs manuellement pour être sûr
    fig, ax = plt.subplots(figsize=(6, 3))
    
    # Fond transparent pour s'adapter au thème Streamlit
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)
    
    # Couleurs des barres et du texte
    bars = ax.bar(names, values, color='#4a90e2')
    
    # Changement couleur des axes et du texte pour la lisibilité (blanc/gris clair)
    ax.tick_params(colors='gray', which='both')  # Couleur des ticks
    for spine in ax.spines.values():
        spine.set_edgecolor('gray') # Couleur des bordures du graph
    
    # Si tu as une légende ou un titre
    ax.set_title("Répartition des Stats", color='gray')
    
    st.pyplot(fig)
