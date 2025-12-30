import streamlit as st
import json

# --- CONFIGURATION ---
with open('config.json', 'r') as f:
    config = json.load(f)

# --- NOUVEAU SYSTÈME DE SAUVEGARDE (SECRETS) ---
# On utilise st.session_state pour stocker les données durant la navigation
if 'user_data' not in st.session_state:
    # On vérifie si une sauvegarde existe dans les "Secrets"
    if "save_data" in st.secrets:
        st.session_state.user_data = json.loads(st.secrets["save_data"])
    else:
        # Premier lancement : Profil neuf
        st.session_state.user_data = {"level": 1, "xp": 0}

user = st.session_state.user_data

def save_progress():
    # Transforme les données en texte pour le stockage
    save_str = json.dumps(user)
    # Note : Sur Streamlit Cloud, la mise à jour des secrets se fait manuellement
    # Pour cette version, on va afficher le code de sauvegarde à copier-coller
    # C'est la méthode la plus simple pour un débutant sans base de données complexe.
    st.session_state.save_str = save_str

# --- LOGIQUE XP ---
def get_xp_needed(lvl):
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    xp = int(coeff * (lvl**config['settings']['exponent']))
    if lvl == 100: xp = xp * 2
    return xp

# --- INTERFACE ---
st.title("⚡ LEVEL CRUSH")

xp_target = get_xp_needed(user['level'])

if st.button(f"Terminer Quête (+215 XP)"):
    user['xp'] += 215
    if user['xp'] >= xp_target:
        user['level'] += 1
        user['xp'] = 0
        st.balloons()
    save_progress()
    st.rerun()

# Affichage du statut
st.metric("Niveau", user['level'])
st.progress(min(user['xp'] / xp_target, 1.0))

# ZONE DE SAUVEGARDE MANUELLE (Temporaire pour la V1)
st.divider()
if 'save_str' in st.session_state:
    st.write("💾 **SAUVEGARDE DÉTECTÉE**")
    st.write("Copie ce code et colle-le dans les 'Secrets' de Streamlit pour ne jamais perdre ta progression :")
    st.code(st.session_state.save_str)
