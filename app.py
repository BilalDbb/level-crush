import streamlit as st
import json
from supabase import create_client, Client

# --- 1. CONNEXION SUPABASE ---
# On récupère les clés dans les Secrets de Streamlit pour la sécurité
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Clés de configuration manquantes ou incorrectes dans les Secrets Streamlit.")
    st.stop()

# --- 2. CONFIGURATION DU JEU ---
# Chargement des règles définies dans ton fichier config.json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    st.error("Le fichier config.json est introuvable sur GitHub.")
    st.stop()

# --- 3. FONCTIONS DE SAUVEGARDE AUTOMATIQUE (SUPABASE) ---
def load_from_supabase(user_id="mon_user_unique"):
    try:
        # On tente de récupérer la donnée dans la table 'profiles'
        response = supabase.table('profiles').select('data').eq('user_id', user_id).execute()
        # Si une donnée existe, on la renvoie
        if response.data and len(response.data) > 0:
            return response.data[0]['data']
    except Exception as e:
        # Si la table n'est pas prête ou erreur de colonne, on affiche l'alerte
        st.warning(f"Note : Impossible de lire la base de données ({e}). Utilisation du profil local.")
    
    # Par défaut (premier lancement ou erreur), on commence au Niveau 1
    return {"level": 1, "xp": 0}

def save_to_supabase(data, user_id="mon_user_unique"):
    try:
        # On enregistre ou met à jour (upsert) la donnée
        supabase.table('profiles').upsert({"user_id": user_id, "data": data}).execute()
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")

# Initialisation de la donnée dans la session Streamlit
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_from_supabase()

user = st.session_state.user_data

# --- 4. LOGIQUE DU MOTEUR XP ---
def get_xp_needed(lvl):
    # Utilisation des coefficients de ta config
    coeff = config['settings']['coeff_low'] if lvl < 5 else config['settings']['coeff_high']
    xp = int(coeff * (lvl**config['settings']['exponent']))
    # Le "mur" du niveau 100 qui double l'exigence
    if lvl == 100:
        xp = xp * 2
    return xp

# --- 5. INTERFACE UTILISATEUR (UI) ---
st.set_page_config(page_title="LEVEL CRUSH", page_icon="⚡")

st.title(f"⚡ {config['settings']['app_name']} : AUTO-SAVE")

xp_target = get_xp_needed(user['level'])

# Affichage des statistiques principales
col1, col2 = st.columns(2)
with col1:
    st.metric("Niveau actuel", user['level'])
with col2:
    st.metric("XP Totale", user['xp'])

# Barre de progression visuelle
progress = min(user['xp'] / xp_target, 1.0)
st.progress(progress)
st.write(f"Progression vers le niveau suivant : {int(progress * 100)}%")

st.divider()

# Bouton d'action pour tester le système
st.subheader("⚔️ Entraînement")
if st.button(f"Terminer une Quête (+215 XP)"):
    user['xp'] += 215
    
    # Vérification de montée de niveau
    if user['xp'] >= xp_target:
        user['level'] += 1
        user['xp'] = 0
        st.balloons()
        st.success(f"Félicitations ! Tu as atteint le niveau {user['level']} !")
    
    # Sauvegarde automatique vers Supabase
    save_to_supabase(user)
    st.rerun()

# Information de débogage (visible seulement pour toi)
with st.expander("🔍 Debugging Data"):
    st.json(user)
