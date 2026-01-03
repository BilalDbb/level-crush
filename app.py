import streamlit as st
import plotly.graph_objects as go
import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Nexus Quotidien", page_icon="⚔️", layout="wide")

# --- STYLES CSS PERSONNALISÉS ---
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #3b82f6;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- GESTION DE L'ÉTAT (SESSION STATE) ---
if 'xp' not in st.session_state:
    st.session_state.xp = 2450
if 'level' not in st.session_state:
    st.session_state.level = 5
if 'log' not in st.session_state:
    st.session_state.log = [
        {"time": "10:30", "text": "Lecture Deep Work complétée", "xp": "+25"},
        {"time": "Hier", "text": "Entraînement physique validé", "xp": "+50"}
    ]

# Données initiales (Uniquement Quotidiennes, pas de date, reset manuel pour le MVP)
if 'tasks' not in st.session_state:
    st.session_state.tasks = [
        {"id": 1, "title": "Lecture Deep Work", "category": "Intellect", "difficulty": "Moyen", "current": 15, "target": 20, "unit": "pages", "streak": 5},
        {"id": 2, "title": "Entraînement 30min", "category": "Physique", "difficulty": "Difficile", "current": 1, "target": 1, "unit": "séance", "streak": 3},
        {"id": 3, "title": "Méditation", "category": "Intellect", "difficulty": "Facile", "current": 0, "target": 10, "unit": "min", "streak": 0},
        {"id": 4, "title": "Dessin", "category": "Créatif", "difficulty": "Facile", "current": 0, "target": 1, "unit": "dessin", "streak": 0},
    ]

# --- FONCTIONS ---
def add_xp(amount, task_title):
    st.session_state.xp += amount
    now = datetime.datetime.now().strftime("%H:%M")
    st.session_state.log.insert(0, {"time": now, "text": f"Quête accomplie : {task_title}", "xp": f"+{amount}"})
    if st.session_state.xp >= 3000:
        st.session_state.level += 1
        st.session_state.xp -= 3000
        st.balloons()

def increment_task(task_index):
    task = st.session_state.tasks[task_index]
    if task['current'] < task['target']:
        st.session_state.tasks[task_index]['current'] += 1
        if st.session_state.tasks[task_index]['current'] == task['target']:
            rewards = {"Facile": 10, "Moyen": 25, "Difficile": 50}
            xp_gain = rewards.get(task['difficulty'], 10)
            add_xp(xp_gain, task['title'])
            st.toast(f"🎉 Quête terminée ! +{xp_gain} XP")

def delete_task(task_index):
    del st.session_state.tasks[task_index]
    st.rerun()

def create_task(title, category, difficulty, target, unit):
    new_id = len(st.session_state.tasks) + 100
    new_task = {
        "id": new_id, "title": title, "category": category, "difficulty": difficulty,
        "current": 0, "target": target, "unit": unit, "streak": 0
    }
    st.session_state.tasks.append(new_task)

# --- INTERFACE ---
col_title, col_stats = st.columns([2, 1])
with col_title:
    st.title("⚔️ Nexus Quotidien")
with col_stats:
    st.metric(label=f"Niveau {st.session_state.level}", value=f"{st.session_state.xp} XP", delta="Objectif: 3000")
    st.progress(min(1.0, st.session_state.xp / 3000))

st.divider()

main_col, side_col = st.columns([2, 1])

with main_col:
    st.subheader("🎯 Quêtes du Jour")
    with st.expander("➕ Créer une nouvelle quête"):
        with st.form("new_quest"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_title = st.text_input("Titre")
                new_cat = st.selectbox("Catégorie", ["Physique", "Intellect", "Social", "Créatif"])
            with c2:
                new_diff = st.selectbox("Difficulté", ["Facile", "Moyen", "Difficile"])
            with c3:
                new_target = st.number_input("Objectif", min_value=1, value=1)
                new_unit = st.text_input("Unité", value="fois")
            if st.form_submit_button("Ajouter") and new_title:
                create_task(new_title, new_cat, new_diff, new_target, new_unit)
                st.rerun()

    if not st.session_state.tasks:
        st.info("Aucune quête active.")
    
    for i, task in enumerate(st.session_state.tasks):
        progress_val = task['current'] / task['target']
        is_done = task['current'] >= task['target']
        
        with st.container():
            c_btn, c_info, c_del = st.columns([1, 4, 0.5])
            with c_btn:
                if not is_done:
                    if st.button("➕", key=f"btn_{task['id']}"):
                        increment_task(i)
                        st.rerun()
                else:
                    st.success("✅")
            with c_info:
                st.markdown(f"**{task['title']}** <span style='color:gray; font-size:0.8em'>({task['category']})</span>", unsafe_allow_html=True)
                st.progress(progress_val)
            with c_del:
                if st.button("🗑️", key=f"del_{task['id']}"):
                    delete_task(i)
            st.markdown("---")

with side_col:
    st.subheader("📊 Équilibre")
    categories = ["Physique", "Intellect", "Social", "Créatif"]
    scores = {cat: 0 for cat in categories}
    counts = {cat: 0 for cat in categories}
    
    for t in st.session_state.tasks:
        counts[t['category']] += 1
        scores[t['category']] += min(1.0, t['current'] / t['target'])

    final_values = []
    hover_texts = []
    for cat in categories:
        val = (scores[cat] / counts[cat] * 100) if counts[cat] > 0 else 0
        final_values.append(val)
        hover_texts.append("Maîtrisé" if val == 100 else "Echec" if val == 0 else "Partiel")

    fig = go.Figure(data=go.Scatterpolar(
        r=final_values, theta=categories, fill='toself',
        name='Progression', line_color='#8b5cf6', hovertext=hover_texts,
        hovertemplate="%{theta}: %{r:.0f}%<br>Statut: %{hovertext}<extra></extra>"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        margin=dict(l=20, r=20, t=20, b=20), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📜 Journal de Bord")
    with st.container(height=300):
        for entry in st.session_state.log:
            st.write(f"✅ **{entry['text']}** :green[{entry['xp']}]")
            st.caption(entry['time'])
