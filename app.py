import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. CONNEXION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur Cloud : {e}")
    st.stop()

# --- 2. LOGIQUE SYSTÈME ---
XP_PER_TASK = 100  # Valeur fixe pour chaque tâche

def get_xp_required(lvl):
    # Formule exponentielle douce pour la montée en niveau
    next_lvl = lvl + 1
    if lvl < 5: return int(200 * (next_lvl**1.2))
    elif 5 <= lvl < 100: return int(25 * (next_lvl**1.2))
    else: return int(int(25 * (100**1.2)) * 10)

def get_total_cumulated_xp(lvl, current_xp):
    total = 0
    for l in range(1, lvl): total += get_xp_required(l)
    return total + current_xp

# --- 3. CONFIGURATION DES TITRES ---
TITLES_DATA = [(1, "Starter", "#DCDDDF"), (3, "Néophyte", "#3498DB"), (6, "Aspirant", "#2ECC71"), (10, "Soldat de Plomb", "#E67E22"), (14, "Gardien de Fer", "#95A5A6"), (19, "Traqueur Silencieux", "#9B59B6"), (24, "Vanguard", "#2980B9"), (30, "Chevalier d'Acier", "#BDC3C7"), (36, "Briseur de Chaînes", "#F39C12"), (43, "Architecte du Destin", "#34495E"), (50, "Légat du Système", "#16A085"), (58, "Commandeur", "#27AE60"), (66, "Seigneur de Guerre", "#C0392B"), (75, "Entité Transcendante", "#F1C40F"), (84, "Demi-Dieu", "#E74C3C"), (93, "Souverain", "#8E44AD"), (100, "LEVEL CRUSHER", "#000000")]

def get_current_title_info(lvl):
    current = TITLES_DATA[0]
    for l_req, name, color in TITLES_DATA:
        if lvl >= l_req: current = (l_req, name, color)
    return current

def get_default_data():
    return {
        "level": 1, "xp": 0, "mode": "Séide", 
        "completed_quests": [], 
        "task_lists": {"Quotidiennes": []}, # On garde la structure dict au cas où tu revoudrais l'hebdo un jour
        "combat_log": [], "xp_history": [], "internal_date": datetime.now().strftime("%Y-%m-%d")
    }

# --- 4. GESTION DES DONNÉES ---
MY_ID = "shadow_monarch_01" 
def load_data():
    try:
        res = supabase.table('profiles').select('data').eq('user_id', MY_ID).execute()
        if res.data:
            d = res.data[0]['data']
            if isinstance(d, str): d = json.loads(d)
            # Nettoyage des vieilles clés si elles existent encore dans la DB
            if "stats" in d: del d["stats"]
            if "task_diffs" in d: del d["task_diffs"]
            if "task_stat_links" in d: del d["task_stat_links"]
            
            # Init clés manquantes
            if "combat_log" not in d: d["combat_log"] = []
            if "xp_history" not in d: d["xp_history"] = []
            return d
    except: pass
    return get_default_data()

def save_data(data):
    supabase.table('profiles').upsert({"user_id": MY_ID, "data": data}).execute()

u = load_data()

def process_xp_change(amount, task_name=None, status="fait"):
    u['xp'] += amount
    log_msg = f"{status.upper()} : {task_name if task_name else 'Action'} ({amount:+d} XP)"
    
    # Gestion Montée de niveau
    while True:
        req = get_xp_required(u['level'])
        if u['xp'] >= req and u['level'] < 100: 
            u['xp'] -= req
            u['level'] += 1
            st.toast(f"🌟 LEVEL UP ! Vous êtes maintenant niveau {u['level']}")
        else: break
        
    # Gestion Descente de niveau (Mode Exalté uniquement)
    if u['mode'] == "Exalté":
        while u['xp'] < 0 and u['level'] > 1: 
            u['level'] -= 1
            u['xp'] += get_xp_required(u['level'])
            st.toast("📉 LEVEL DOWN...")

    u["xp_history"].append({"date": u["internal_date"], "xp_cumul": get_total_cumulated_xp(u['level'], u['xp']), "status": status})
    u["combat_log"].insert(0, f"[{u['internal_date']}] {log_msg}")
    u["combat_log"] = u["combat_log"][:15]

# --- 5. INTERFACE ---
st.set_page_config(page_title="LEVEL CRUSH", layout="wide")
curr_l_req, title_name, title_color = get_current_title_info(u['level'])
glow_color = "#00FFCC" if title_name == "LEVEL CRUSHER" else title_color

# Header (Niveau & Titre)
st.markdown(f'<div style="text-align:center;padding:10px;"><span style="color:white;font-size:1.1em;">NIV.{u["level"]}</span> <div style="display:inline-block;margin-left:12px;padding:4px 18px;border:2px solid {glow_color};border-radius:20px;box-shadow:0 0 12px {glow_color};background:{title_color};"><b style="color:{"black" if title_name=="Starter" else "#00FFCC" if title_name=="LEVEL CRUSHER" else "white"};font-size:1.3em;">{title_name}</b></div></div>', unsafe_allow_html=True)

# Barre XP globale
req_xp = get_xp_required(u['level'])
st.progress(min(max(u['xp']/req_xp, 0.0), 1.0))
st.caption(f"XP : **{u['xp']} / {req_xp}** (Prochain niveau à {req_xp - u['xp']})")

tabs = st.tabs(["⚔️ Quêtes", "📈 Progression", "⚙️ Config"])

with tabs[0]:
    # --- SECTION QUÊTES ---
    tsks = u["task_lists"].get("Quotidiennes", [])
    
    st.subheader(f"📅 Missions du Jour ({len(tsks)})")
    
    if tsks:
        for i, t in enumerate(tsks):
            done = t in u["completed_quests"]
            
            # Layout simplifié : Check | Titre | Bouton Delete (si besoin)
            container = st.container()
            c1, c2, c3 = container.columns([0.5, 4, 0.5])
            
            # 1. Action Button
            with c1:
                if done:
                    st.success("✔")
                else:
                    if st.button("⬜", key=f"check_{i}"):
                        process_xp_change(XP_PER_TASK, t, "fait")
                        u["completed_quests"].append(t)
                        save_data(u)
                        st.rerun()
            
            # 2. Titre Tâche
            with c2:
                if done:
                    st.markdown(f"~~{t}~~", unsafe_allow_html=True)
                else:
                    st.markdown(f"**{t}**")

            # 3. Penalité (Si mode Exalté et pas fait)
            if u['mode'] == "Exalté" and not done:
                 if c3.button("✖", key=f"fail_{i}", help="Déclarer l'échec (-XP)"):
                     process_xp_change(-XP_PER_TASK, t, "echec")
                     save_data(u)
                     st.rerun()
            
            st.divider()
    else:
        st.info("Aucune mission active. Ajoutez-en une dans l'onglet Config !")

    st.subheader("🛡️ Journal de Bord")
    for log in u["combat_log"]: st.caption(log)

with tabs[1]:
    # --- SECTION STATS SIMPLIFIÉES ---
    st.markdown("<h3 style='text-align:center;'>Courbe de Puissance</h3>", unsafe_allow_html=True)
    if u["xp_history"]:
        df = pd.DataFrame(u["xp_history"])
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        # Ligne principale
        fig.add_trace(go.Scatter(x=df['date'], y=df['xp_cumul'], mode='lines', line=dict(color='#00FFCC', width=3), name="XP Total"))
        
        # Points de succès/échec
        succes = df[df['status'] == 'fait']
        echecs = df[df['status'].isin(['echec', 'rouge'])]
        
        if not succes.empty:
            fig.add_trace(go.Scatter(x=succes['date'], y=succes['xp_cumul'], mode='markers', marker=dict(color='#00FFCC', size=6), name="Succès"))
        if not echecs.empty:
            fig.add_trace(go.Scatter(x=echecs['date'], y=echecs['xp_cumul'], mode='markers', marker=dict(color='red', size=6), name="Echec"))

        fig.update_layout(template="plotly_dark", height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("En attente de données...")
        
    # Petit rappel des titres
    with st.expander("Voir les Rangs"):
        items_html = "".join([f'<div style="min-width:90px;text-align:center;opacity:{"1" if u["level"]>=l else "0.3"};margin-right:15px;"><div style="width:14px;height:14px;background:{"#333" if u["level"]<l else c};border-radius:50%;margin:0 auto;border:1px solid #555;"></div><p style="font-size:11px;color:{"#333" if u["level"]<l else c};margin-top:8px;font-weight:bold;">{n}</p><p style="font-size:9px;color:#666;">Niv.{l}</p></div>' for l,n,c in TITLES_DATA])
        components.html(f'<style>body{{background:transparent;margin:0;}}.scroll{{display:flex;overflow-x:auto;padding:10px 5px;scrollbar-width:thin;}}</style><div class="scroll">{items_html}</div>', height=100)

with tabs[2]:
    # --- SECTION CONFIG ---
    st.subheader("Paramètres")
    
    c_mode, c_add = st.columns([1, 2])
    
    with c_mode:
        nm = st.radio("Difficulté", ["Séide", "Exalté"], index=["Séide", "Exalté"].index(u["mode"]), help="Exalté = Vous pouvez perdre de l'XP.")
        if nm != u["mode"]: u["mode"] = nm; save_data(u); st.rerun()

    with c_add:
        st.write("**Ajouter une mission**")
        with st.form("add_task"):
            col_in, col_btn = st.columns([3, 1])
            new_task = col_in.text_input("Intitulé", label_visibility="collapsed", placeholder="Ex: Lire 10 pages")
            if col_btn.form_submit_button("Ajouter"):
                if new_task:
                    u["task_lists"]["Quotidiennes"].append(new_task)
                    save_data(u)
                    st.rerun()

    st.divider()
    st.write("**Gérer les missions existantes**")
    
    # Gestion simple de la liste
    tasks_to_keep = []
    has_changed = False
    
    for t in u["task_lists"]["Quotidiennes"]:
        c1, c2 = st.columns([4, 1])
        new_name = c1.text_input("Nom", t, key=f"edit_{t}", label_visibility="collapsed")
        
        # Si on change le nom
        if new_name != t:
            tasks_to_keep.append(new_name)
            has_changed = True
        # Si on clique sur supprimer
        elif c2.button("🗑️", key=f"del_conf_{t}"):
            has_changed = True
            # On ne l'ajoute pas à tasks_to_keep, donc elle saute
        else:
            tasks_to_keep.append(t)
            
    if has_changed:
        u["task_lists"]["Quotidiennes"] = tasks_to_keep
        save_data(u)
        st.rerun()

with st.sidebar:
    st.header("⏳ Temps")
    
    if st.button("🌙 Fin de journée (Sauter)"):
        # Calcul des pénalités si Exalté
        if u['mode'] == "Exalté":
            missed = [t for t in u["task_lists"]["Quotidiennes"] if t not in u["completed_quests"]]
            if missed:
                penalty = len(missed) * XP_PER_TASK
                process_xp_change(-penalty, "Journée incomplète", "rouge")
        
        # Passage au lendemain
        u["internal_date"] = (datetime.strptime(u["internal_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        u["completed_quests"] = [] # Reset des checkbox
        save_data(u)
        st.rerun()
        
    st.divider()
    if st.button("💀 HARD RESET"): 
        save_data(get_default_data())
        st.rerun()
