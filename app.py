import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from supabase import create_client, Client

# ==============================================================================
# BLOC 1 : CONFIGURATION & CSS (Le visuel)
# ==============================================================================
st.set_page_config(page_title="Level Crush", layout="centered")

def inject_custom_css():
    st.markdown("""
    <style>
    /* --- STYLE CARTE (Quêtes) --- */
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
        display: flex; justify-content: space-between; align-items: center;
        transition: transform 0.2s;
    }
    .quest-item:hover { transform: translateX(5px); }

    /* --- MODE SOMBRE (Ajustements auto) --- */
    @media (prefers-color-scheme: dark) {
        .quest-item {
            background-color: #262730;
            color: #ffffff !important;
            border-left-color: #ffbd45;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .streamlit-expanderHeader { background-color: #262730 !important; color: #fff !important; }
        .streamlit-expanderContent p { color: #e0e0e0 !important; }
        button { border-color: rgba(255,255,255,0.2) !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# BLOC 2 : BACKEND & DATA (La logique BDD isolée)
# ==============================================================================
@st.cache_resource
def init_supabase():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        return None

supabase = init_supabase()

def db_get_taches():
    if not supabase: return []
    try: return supabase.table("taches").select("*").order("id").execute().data
    except: return []

def db_add_tache(nom, xp):
    if not supabase: return
    try: supabase.table("taches").insert({"nom": nom, "xp": xp}).execute()
    except: st.error("Erreur ajout tâche")

def db_delete_tache(tid):
    if not supabase: return
    try: supabase.table("taches").delete().eq("id", tid).execute()
    except: st.error("Erreur suppression")

def db_log(msg):
    if not supabase: return
    try: supabase.table("journal").insert({"date": str(datetime.date.today()), "message": msg}).execute()
    except: pass

def db_reset(mode="soft"):
    if not supabase: return
    try:
        if mode == "hard":
            # Logique hard restart (supprime tout)
            supabase.table("taches").delete().neq("id", 0).execute()
            supabase.table("journal").delete().neq("id", 0).execute()
        else:
            # Exemple Reset simple (supprime juste les tâches du jour)
            supabase.table("taches").delete().neq("id", 0).execute()
    except Exception as e: st.error(f"Erreur Reset: {e}")

def db_get_journal():
    if not supabase: return []
    try: return supabase.table("journal").select("*").order("date", desc=True).execute().data
    except: return []

# ==============================================================================
# BLOC 3 : COMPOSANTS UI (L'affichage par onglet)
# ==============================================================================

def render_tab_quetes():
    st.subheader("Quêtes actives")
    taches = db_get_taches()
    
    if not taches:
        st.info("Aucune quête. Ajoute-en une dans 'Config'.")
        return

    for t in taches:
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"""
            <div class="quest-item">
                <span>{t['nom']}</span>
                <span style="opacity:0.7;">+{t['xp']} XP</span>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.write("") 
            if st.button("✅", key=f"v_{t['id']}"):
                db_log(f"Quête terminée : {t['nom']} (+{t['xp']} XP)")
                db_delete_tache(t['id'])
                st.rerun()

def render_tab_progression():
    st.subheader("Statistiques")
    
    # Données (Statiques pour l'instant, à relier à la BDD plus tard)
    data = {'Force': 20, 'Intel': 35, 'Endu': 15, 'Charisme': 10}
    
    # Graphique Matplotlib
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f']
    ax.bar(data.keys(), data.values(), color=colors)
    
    # Style adaptatif (Gris neutre)
    TC = '#909090'
    ax.tick_params(colors=TC, which='both')
    for spine in ax.spines.values(): spine.set_edgecolor(TC)
    ax.set_title("Attributs", color=TC)
    
    # Légende manuelle (Hack pour visibilité sombre/clair)
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=n) for c, n in zip(colors, data.keys())]
    leg = ax.legend(handles=legend_elements, loc='upper right', frameon=False)
    for text in leg.get_texts(): text.set_color(TC)
    
    st.pyplot(fig)
    
    st.divider()
    st.subheader("Historique")
    logs = db_get_journal()
    with st.expander("📖 Voir le journal", expanded=False):
        if logs:
            for l in logs: st.write(f"- **{l['date']}** : {l['message']}")
        else: st.write("Rien à signaler.")

def render_tab_config():
    st.subheader("Ajouter")
    # Alignement propre Input/Bouton
    c_in, c_btn = st.columns([4, 1])
    with c_in:
        new_t = st.text_input("Tâche", placeholder="Ex: Lire 10 min", label_visibility="collapsed")
    with c_btn:
        go_add = st.button("Ajouter", use_container_width=True)
    
    if go_add and new_t:
        db_add_tache(new_t, 10)
        st.success(f"Ajouté : {new_t}")
        st.rerun()
        
    st.divider()
    st.subheader("Gestion")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⏩ Sauter Jour", use_container_width=True):
            db_log("Journée sautée.")
            st.success("Repos validé.")
    with c2:
        if st.button("🔄 Reset", use_container_width=True, type="primary"):
            db_reset("soft")
            st.rerun()
    with c3:
        if st.button("💀 Hard Restart", use_container_width=True, type="primary"):
            db_reset("hard")
            st.rerun()

# ==============================================================================
# BLOC 4 : MAIN (L'exécution)
# ==============================================================================
def main():
    inject_custom_css()
    st.title("Level Crush")
    
    if not supabase:
        st.error("⚠️ Pas de connexion Supabase detected.")
    
    t1, t2, t3 = st.tabs(["📜 Quêtes", "📈 Progression", "⚙️ Config"])
    
    with t1: render_tab_quetes()
    with t2: render_tab_progression()
    with t3: render_tab_config()

if __name__ == "__main__":
    main()
