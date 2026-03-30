import streamlit as st
import pandas as pd
from bilim_engine import 

# 1. СТИЛЬ ЖӘНЕ ДИЗАЙН (CSS)
st.set_page_config(page_title="Aqbobek Lyceum", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 10px; background: #0c1e3d; color: white; }
    </style>
""", unsafe_allow_html=True)

# 2. СЕССИЯНЫ ИНИЦИАЛИЗАЦИЯЛАУ
if "bilim_data" not in st.session_state:
    st.session_state.bilim_data = build_initial_mock_bilim()
if "users_db" not in st.session_state:
    st.session_state.users_db = {"admin": {"pw": "123", "role": "admin", "name": "Администратор"}}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 3. АВТОРИЗАЦИЯ ЖӘНЕ ТІРКЕЛУ
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🎓 Aqbobek Portal")
        tab1, tab2 = st.tabs(["Кіру", "Тіркелу"])
        
        with tab1:
            u = st.text_input("Логин")
            p = st.text_input("Пароль", type="password")
            if st.button("Войти"):
                if u in st.session_state.users_db and st.session_state.users_db[u]["pw"] == p:
                    st.session_state.logged_in = True
                    st.session_state.u_info = st.session_state.users_db[u]
                    st.rerun()
                else: st.error("Қате!")

        with tab2:
            new_u = st.text_input("Жаңа логин")
            new_p = st.text_input("Пароль орнату", type="password")
            new_n = st.text_input("Атыңыз (мысалы: Айым К.)")
            new_r = st.selectbox("Рөліңіз", ["student", "teacher", "parent"])
            if st.button("Зарегистрироваться"):
                st.session_state.users_db[new_u] = {"pw": new_p, "role": new_r, "name": new_n}
                st.success("Дайын! Енді 'Кіру' бөліміне өтіңіз.")

# 4. НЕГІЗГІ ПАНЕЛЬ (ЖҮЙЕГЕ КІРГЕННЕН КЕЙІН)
else:
    role = st.session_state.u_info["role"]
    name = st.session_state.u_info["name"]
    
    st.sidebar.title("Aqbobek Lyceum")
    st.sidebar.write(f"Пайдаланушы: **{name}** ({role})")
    menu = st.sidebar.radio("Мәзір", ["🏠 Басты бет", "📊 Аналитика", "🏆 Лидерборд", "🤖 Alaman AI"])

    if st.sidebar.button("Шығу (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    # --- БЕТТЕР ---
    if menu == "🏠 Басты бет":
        st.header("🏠 Жаңалықтар лентасы")
        for n in st.session_state.bilim_data["news"]:
            st.markdown(f"<div class='main-card'><h3>{n['title']}</h3><p>{n['body']}</p><small>{n['date']}</small></div>", unsafe_allow_html=True)

    elif menu == "🏆 Лидерборд":
        st.header("🏆 Оқушылар рейтингі (Геймификация)")
        df = get_leaderboard_data(st.session_state.bilim_data)
        st.table(df)
        st.balloons()

    elif menu == "📊 Аналитика":
        st.header("📊 Оқу үлгерімі")
        if role == "student":
            stu = next((s for s in st.session_state.bilim_data["students"] if name in s["full_name"]), None)
            if stu:
                st.write(f"Сенің қатысу көрсеткішің: {stu['attendance']['present']}%")
                st.line_chart([g["score"] for g in stu["grades_timeline"]])
            else: st.info("Мәлімет табылмады. Тіркелгенде атыңызды дұрыс жазыңыз.")
        else:
            st.write("Барлық сыныптар бойынша есеп мұғалімге қолжетімді.")

    elif menu == "🤖 Alaman AI":
        st.header("🤖 Alaman Mentor (Smart Logic)")
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])
            
        if prompt := st.chat_input("Сұрақ қойыңыз..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            
            reply = get_alaman_ai_reply(prompt, name, role, st.session_state.bilim_data)
            
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"): st.write(reply)