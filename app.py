import streamlit as st
import json

# --- CHARGEMENT DES DONNÉES ---
# On ouvre le fichier JSON pour lire tes réglages (Base XP, etc.)
with open('config.json', 'r') as f:
    config = json.load(f)

# --- LOGIQUE MATHÉMATIQUE ---
# Cette fonction calcule l'XP nécessaire pour passer au niveau suivant
def get_xp_needed(level):
    # On utilise le coefficient 200 si le niveau est bas (<5), sinon 25
    coeff = config['settings']['coeff_low'] if level < 5 else config['settings']['coeff_high']
    
    # Formule : Coefficient * (Niveau puissance 1.2)
    xp = coeff * (level**config['settings']['exponent'])
    
    # Si c'est le niveau ultime (100), on double la difficulté
    if level == 100:
        xp = xp * 2
    return int(xp)

# --- INTERFACE UTILISATEUR (UI) ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")

# Titre stylé avec le nom de l'app
st.title(f"⚡ {config['settings']['app_name']}")

# Sidebar (Barre latérale) pour les infos du Chasseur
with st.sidebar:
    st.header("👤 Statut du Chasseur")
    level = st.number_input("Niveau actuel", min_value=1, value=1)
    st.write(f"Prochain palier de Titre : **{min([l for l in config['progression']['title_unlock_levels'] if l > level])}**")
    st.divider()
    st.info(f"Mode : {config['settings']['penalty_mode']}")

# Affichage de l'XP nécessaire
xp_target = get_xp_needed(level)
st.metric(label="Objectif XP Niveau Suivant", value=f"{xp_target} XP")

st.write("---")
st.subheader("📜 Quêtes du jour")
st.info("Système en cours d'initialisation... Bientôt, tu pourras valider tes tâches ici !")
