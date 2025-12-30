import streamlit as st
import json
import os

# --- 1. CONFIGURATION & CHARGEMENT ---
# On charge les règles du jeu que tu as définies (Base XP, etc.)
with open('config.json', 'r') as f:
    config = json.load(f)

# Fonction pour charger ta progression (ton niveau, ton XP actuelle)
def load_data():
    if os.path.exists('save.json'):
        with open('save.json', 'r') as f:
            return json.load(f)
    # Si le fichier n'existe pas encore (première fois), on crée un profil neuf
    return {"level": 1, "xp": 0, "logs": []}

# Fonction pour enregistrer ta progression
def save_data(data):
    with open('save.json', 'w') as f:
        json.dump(data, f, indent=4)

# Initialisation de la "Session" (C'est la mémoire vive de l'app tant que l'onglet est ouvert)
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_data()

user = st.session_state.user_data

# --- 2. LOGIQUE DE CALCUL (MOTEUR XP) ---
def get_xp_needed(lvl):
    # Tes règles : Coeff 200 avant lvl 5, sinon 25
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    xp = int(coeff * (lvl**config['settings']['exponent']))
    # Le mur du niveau 100 (x2)
    if lvl == 100:
        xp = xp * 2
    return xp

# --- 3. INTERFACE MOBILE-FIRST ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")

# Titre principal
st.title(f"⚡ {config['settings']['app_name']}")

# Sidebar : Le statut du Chasseur
with st.sidebar:
    st.header("👤 Statut")
    st.write(f"Niveau : **{user['level']}**")
    
    # Calcul de la barre de progression
    xp_target = get_xp_needed(user['level'])
    progress = user['xp'] / xp_target
    st.progress(min(progress, 1.0))
    st.write(f"XP : {user['xp']} / {xp_target}")
    
    if st.button("Réinitialiser l'expérience"):
        st.warning("Es-tu sûr de vouloir sacrifier ta puissance ?")
        # Ici on ajoutera la citation de validation plus tard

# Section Quêtes
st.header("📜 Quêtes")
# On crée un bouton simple pour tester le gain d'XP
st.write("Valider une tâche quotidienne (Poids 1)")
if st.button("Terminer la quête (+215 XP)"):
    user['xp'] += 215 # Gain de base
    
    # Logique de montée de niveau
    if user['xp'] >= xp_target:
        user['level'] += 1
        user['xp'] = 0 # On remet l'XP à zéro pour le nouveau niveau
        st.balloons() # Animation de fête
        st.success(f"RANG SUPÉRIEUR ! Tu es maintenant niveau {user['level']} !")
    
    # Sauvegarde immédiate
    save_data(user)
    st.rerun() # On rafraîchit l'affichage
