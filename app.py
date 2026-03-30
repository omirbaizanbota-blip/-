from __future__ import annotations
import copy
import uuid
import json
import os
import time
import base64
from datetime import datetime
import pandas as pd
import streamlit as st
from bilim_engine import (
    MOCK_NEWS_SEED,
    alaman_bot_reply,
    alaman_opening_message,
    build_initial_mock_bilim,
    class_performance_percent,
    generate_director_ai_report,
    generate_schedule_conflict_free,
    get_student_by_id,
    knowledge_graph_status,
    predict_next_soch,
    sort_news_desc,
    student_performance_trend,
    students_ranking,
    students_with_anomaly_drop,
    weekly_parent_summary,
)

PRIMARY = "#0c1e3d"
ACCENT = "#3d8bfd"
CARD = "#ffffff"
MUTED = "#64748b"
BADGE_CSS = {
    "red": ("#fee2e2", "#b91c1c"),
    "green_bright": ("#bbf7d0", "#15803d"),
    "green_salad": ("#ecfccb", "#4d7c0f"),
    "orange": ("#ffedd5", "#c2410c"),
}
PLACEHOLDER_IMG = "https://via.placeholder.com/600x400"
USERS_DB_FILE = "users_db.json"
NEWS_DB_FILE = "news_db.json"
MESSAGES_DB_FILE = "messages_db.json"
BILIM_DB_FILE = "bilim_data.json"

def load_users() -> dict:
    if os.path.exists(USERS_DB_FILE):
        try:
            with open(USERS_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    default_users = {
        "admin": {"password": "ad123", "role": "admin", "name": "Администратор", "class_name": None},
        "student": {"password": "s123", "role": "student", "name": "Айым К.", "student_id": "stu_002", "class_name": "10A"},
        "teacher": {"password": "t123", "role": "teacher", "name": "Ерлан Сатыбалды", "class_name": "10A"},
        "parent": {"password": "p123", "role": "parent", "name": "Родитель (Айым)", "child_student_id": "stu_002", "class_name": "10A"},
    }
    save_users(default_users)
    return default_users

def save_users(users_dict: dict) -> None:
    with open(USERS_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=2)

def load_news() -> list:
    if os.path.exists(NEWS_DB_FILE):
        try:
            with open(NEWS_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if "image_data" in item and isinstance(item["image_data"], str):
                            item["image_data"] = base64.b64decode(item["image_data"])
                        if "video_data" in item and isinstance(item["video_data"], str):
                            item["video_data"] = base64.b64decode(item["video_data"])
                    return data
        except (json.JSONDecodeError, IOError):
            pass
    default_news = copy.deepcopy(MOCK_NEWS_SEED)
    save_news(default_news)
    return default_news

def save_news(news_list: list) -> None:
    news_to_save = []
    for item in news_list:
        item_copy = item.copy()
        if "image_data" in item_copy and item_copy["image_data"]:
            item_copy["image_data"] = base64.b64encode(item_copy["image_data"]).decode("utf-8")
        if "video_data" in item_copy and item_copy["video_data"]:
            item_copy["video_data"] = base64.b64encode(item_copy["video_data"]).decode("utf-8")
        news_to_save.append(item_copy)
    with open(NEWS_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(news_to_save, f, ensure_ascii=False, indent=2)

def load_messages() -> list:
    if os.path.exists(MESSAGES_DB_FILE):
        try:
            with open(MESSAGES_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_messages(messages: list) -> None:
    with open(MESSAGES_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def load_bilim() -> dict:
    if os.path.exists(BILIM_DB_FILE):
        try:
            with open(BILIM_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return build_initial_mock_bilim()

def save_bilim(bilim_data: dict) -> None:
    with open(BILIM_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(bilim_data, f, ensure_ascii=False, indent=2)

def get_bilim() -> dict:
    return st.session_state.bilim_data

def sync_bilim_with_users() -> None:
    """Синхронизирует bilim_data с users_db: добавляет отсутствующих учеников."""
    bilim = st.session_state.bilim_data
    users = st.session_state.users_db
    existing_ids = {s["id"] for s in bilim["students"]}
    for login, data in users.items():
        if data.get("role") == "student":
            student_id = data.get("student_id", login)
            if student_id not in existing_ids:
                bilim["students"].append({
                    "id": student_id,
                    "full_name": data["name"],
                    "class_id": data.get("class_name", "10A"),
                    "grades_timeline": [],
                    "attendance": {"present": 0, "absent": 0, "late": 0, "sick": 0}
                })
    st.session_state.bilim_data = bilim
    save_bilim(bilim)

def add_grade_to_student(student_id: str, date_str: str, topic: str, score: int) -> None:
    bilim = st.session_state.bilim_data
    student = None
    for s in bilim["students"]:
        if s["id"] == student_id:
            student = s
            break
    if not student:
        # Создаём профиль, если его нет
        users = st.session_state.users_db
        for login, data in users.items():
            if data.get("role") == "student" and data.get("student_id") == student_id:
                student = {
                    "id": student_id,
                    "full_name": data["name"],
                    "class_id": data.get("class_name", "10A"),
                    "grades_timeline": [],
                    "attendance": {"present": 0, "absent": 0, "late": 0, "sick": 0}
                }
                bilim["students"].append(student)
                break
    if student:
        student["grades_timeline"].append({
            "date": date_str,
            "topic": topic,
            "score": score
        })
        st.session_state.bilim_data = bilim
        save_bilim(bilim)

def crm_css() -> None:
    st.markdown(f"""
        <style>
            html, body, [class*="css"] {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important; }}
            .stApp {{ background: linear-gradient(135deg, #e8eef7 0%, #f0f4fa 50%, #e4ecf7 100%); }}
            .crm-header {{
                background: linear-gradient(90deg, {PRIMARY} 0%, #152a52 100%);
                color: #fff;
                padding: 1.35rem 1.75rem;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(12, 30, 61, 0.22);
                margin-bottom: 1.75rem;
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                align-items: center;
            }}
            .crm-header h1 {{ margin: 0; font-size: clamp(1.2rem, 5vw, 1.6rem); font-weight: 700; white-space: nowrap; }}
            .crm-header p {{ margin: 0; opacity: 0.9; font-size: clamp(0.8rem, 3vw, 0.95rem); white-space: nowrap; }}
            .crm-card {{ background: {CARD}; border-radius: 20px; padding: 1.5rem 1.75rem; box-shadow: 0 4px 24px rgba(12, 30, 61, 0.08); border: 1px solid rgba(12, 30, 61, 0.06); margin-bottom: 1.85rem; }}
            .feed-wrap {{ max-width: 560px; margin: 0 auto; }}
            .feed-card {{ background: #fff; border-radius: 20px; overflow: hidden; box-shadow: 0 6px 28px rgba(12, 30, 61, 0.1); margin-bottom: 2rem; border: 1px solid rgba(12, 30, 61, 0.07); }}
            .feed-card h2 {{ color: {PRIMARY}; padding: 1rem 1.25rem 0.25rem; margin: 0; font-size: 1.35rem; }}
            .feed-card .meta {{ color: {MUTED}; padding: 0 1.25rem 0.75rem; font-size: 0.9rem; }}
            .feed-card img, .feed-card video {{ width: 100%; display: block; max-height: 420px; object-fit: cover; }}
            .feed-card .body {{ padding: 1rem 1.25rem 1.35rem; color: #334155; line-height: 1.55; }}
            .risk-badge {{ display: inline-block; padding: 0.3rem 0.85rem; border-radius: 999px; font-weight: 600; font-size: 0.88rem; }}
            .risk-on {{ background: #fee2e2; color: #b91c1c; }}
            .risk-off {{ background: #dcfce7; color: #166534; }}
            div[data-testid="stSidebar"] {{ background: linear-gradient(180deg, {PRIMARY} 0%, #132447 100%); }}
            div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] label {{ color: #e2e8f0 !important; }}
            .login-box {{ max-width: 420px; margin: 3rem auto; padding: 2.5rem; background: #fff; border-radius: 20px; box-shadow: 0 16px 48px rgba(12, 30, 61, 0.12); }}
            .login-title {{ text-align: center; color: {PRIMARY}; font-size: 1.75rem; font-weight: 800; margin-bottom: 1.75rem; }}
            .login-shell {{ min-height: 88vh; display: flex; align-items: center; justify-content: center; padding: 1rem; }}
            div[data-testid="stSidebar"] label span {{ font-weight: 500; letter-spacing: 0.02em; }}
            div[data-testid="stSidebar"] .stRadio > div {{ gap: 0.35rem; }}
            div[class*="st-key-fab_alaman"] {{ position: fixed !important; bottom: 24px !important; right: 20px !important; z-index: 999999 !important; width: auto !important; }}
            div[class*="st-key-fab_alaman"] button {{ border-radius: 50% !important; width: 58px !important; min-width: 58px !important; height: 58px !important; font-size: 1.45rem !important; box-shadow: 0 10px 28px rgba(61, 139, 253, 0.42); }}
            .student-mega .feed-card h2 {{ font-size: clamp(1.75rem, 4vw, 2.35rem) !important; }}
            .student-mega .feed-card .body {{ font-size: clamp(1.1rem, 2.5vw, 1.4rem) !important; }}
            .student-mega .feed-card .meta {{ font-size: 1rem !important; }}
            div[data-testid="stDialog"] {{ border-radius: 20px; }}
            @media (max-width: 640px) {{
                .crm-header h1, .crm-header p {{ white-space: normal; text-align: center; width: 100%; }}
                .crm-header {{ flex-direction: column; gap: 0.5rem; text-align: center; }}
            }}
        </style>
    """, unsafe_allow_html=True)

def student_hide_sidebar_css() -> None:
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] { visibility: hidden !important; min-width: 0 !important; width: 0 !important; }
            div[data-testid="stSidebarCollapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

def login_hide_sidebar_css() -> None:
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] { display: none !important; visibility: hidden !important; width: 0 !important; min-width: 0 !important; }
            div[data-testid="stSidebarCollapsedControl"] { display: none !important; }
            header[data-testid="stHeader"] { background: transparent; }
            .block-container { padding-top: 2rem !important; max-width: 520px !important; }
        </style>
    """, unsafe_allow_html=True)

def init_app_state() -> None:
    if "users_db" not in st.session_state:
        st.session_state.users_db = load_users()
    if "bilim_data" not in st.session_state:
        st.session_state.bilim_data = load_bilim()
    if "news_items" not in st.session_state:
        st.session_state.news_items = load_news()
    if "admin_schedule" not in st.session_state:
        st.session_state.admin_schedule = None
    if "director_report" not in st.session_state:
        st.session_state.director_report = ""
    if "alaman_messages" not in st.session_state:
        st.session_state.alaman_messages = []
    if "fab_chat_open" not in st.session_state:
        st.session_state.fab_chat_open = False
    if "news_likes" not in st.session_state:
        st.session_state.news_likes = {}
    if "teacher_show_ranking" not in st.session_state:
        st.session_state.teacher_show_ranking = False
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_login" not in st.session_state:
        st.session_state.user_login = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "display_name" not in st.session_state:
        st.session_state.display_name = None
    if "current_news_index" not in st.session_state:
        st.session_state.current_news_index = 0
    if "last_news_switch" not in st.session_state:
        st.session_state.last_news_switch = time.time()
    if "messages" not in st.session_state:
        st.session_state.messages = load_messages()
    # Синхронизация bilim_data с пользователями при старте
    sync_bilim_with_users()

def logout() -> None:
    st.session_state.logged_in = False
    st.session_state.user_login = None
    st.session_state.user_role = None
    st.session_state.display_name = None
    st.rerun()

def render_registration() -> None:
    USERS = st.session_state.users_db
    st.markdown('<p class="login-title">Регистрация в Portal</p>', unsafe_allow_html=True)
    with st.form("reg_form"):
        new_u = st.text_input("Придумайте Логин")
        new_p = st.text_input("Придумайте Пароль", type="password")
        new_n = st.text_input("Ваше ФИО")
        new_r = st.selectbox("Ваша роль", ["student", "teacher", "parent"])
        class_name = st.text_input("Ваш класс (например, 10A)", value="10A")
        sid = st.text_input("Student ID (если есть)", value="")
        submit = st.form_submit_button("Зарегистрироваться", use_container_width=True)
        if submit:
            if new_u in USERS:
                st.error("Этот логин уже занят!")
            elif not new_u or not new_p:
                st.warning("Заполните поля логина и пароля")
            else:
                student_id = sid.strip() if sid.strip() else str(uuid.uuid4())[:8]
                USERS[new_u] = {
                    "password": new_p,
                    "role": new_r,
                    "name": new_n,
                    "class_name": class_name,
                    "student_id": student_id if new_r == "student" else None,
                    "child_student_id": student_id if new_r == "parent" else None,
                }
                save_users(USERS)
                # Если регистрируется ученик, добавляем его в bilim_data
                if new_r == "student":
                    bilim = st.session_state.bilim_data
                    bilim["students"].append({
                        "id": student_id,
                        "full_name": new_n,
                        "class_id": class_name,
                        "grades_timeline": [],
                        "attendance": {"present": 0, "absent": 0, "late": 0, "sick": 0}
                    })
                    st.session_state.bilim_data = bilim
                    save_bilim(bilim)
                st.success("Аккаунт создан! Теперь войдите во вкладке 'Вход'")

def current_student() -> dict | None:
    ur = st.session_state.get("user_role")
    USERS = st.session_state.users_db
    if ur == "student":
        sid = USERS[st.session_state.user_login].get("student_id", "stu_002")
        return get_student_by_id(get_bilim(), sid)
    if ur == "parent":
        sid = USERS[st.session_state.user_login].get("child_student_id", "stu_002")
        return get_student_by_id(get_bilim(), sid)
    return None

def render_login() -> None:
    USERS = st.session_state.users_db
    login_hide_sidebar_css()
    crm_css()
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="login-shell"><div class="login-box">', unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["Вход", "Регистрация"])
        with tab_log:
            st.markdown('<p class="login-title">Aqbobek Lyceum</p>', unsafe_allow_html=True)
            login = st.text_input("Логин", key="login_field")
            password = st.text_input("Пароль", type="password", key="pwd_field")
            if st.button("Войти", type="primary", use_container_width=True, key="btn_login"):
                u = USERS.get(login.strip())
                if u and u["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_login = login.strip()
                    st.session_state.user_role = u["role"]
                    st.session_state.display_name = u["name"]
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль")
        with tab_reg:
            render_registration()
        st.markdown("</div></div>", unsafe_allow_html=True)

def merged_news() -> list[dict]:
    return sort_news_desc(st.session_state.news_items)

def render_news_feed_content(*, mega_fonts: bool) -> None:
    wrap_class = "feed-wrap student-mega" if mega_fonts else "feed-wrap"
    st.markdown(f'<div class="{wrap_class}">', unsafe_allow_html=True)
    news_list = merged_news()
    if not news_list:
        st.info("Нет новостей")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    current_time = time.time()
    if current_time - st.session_state.last_news_switch >= 5:
        st.session_state.current_news_index = (st.session_state.current_news_index + 1) % len(news_list)
        st.session_state.last_news_switch = current_time
        st.rerun()
    n = news_list[st.session_state.current_news_index]
    nid = str(n.get("id", ""))
    dt = n.get("published_at", "")[:16].replace("T", " ")
    st.markdown(f'<div class="feed-card"><h2>{n.get("title", "")}</h2><div class="meta">{dt}</div>', unsafe_allow_html=True)
    if n.get("image_data"):
        st.image(n["image_data"], use_container_width=True)
    elif n.get("video_data"):
        st.video(n["video_data"])
    elif n.get("image_url"):
        st.image(n["image_url"], use_container_width=True)
    elif n.get("video_url"):
        st.video(n["video_url"])
    else:
        st.image(PLACEHOLDER_IMG, use_container_width=True)
    st.markdown(f'<div class="body">{n.get("body", "")}</div></div>', unsafe_allow_html=True)
    likes = int(st.session_state.news_likes.get(nid, 0))
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button(f"♡ {likes}" if likes else "♡", key=f"like_{nid}", help="Нравится"):
            st.session_state.news_likes[nid] = likes + 1
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def _best_class_banner_html() -> str:
    perf = class_performance_percent(get_bilim())
    if not perf:
        return ""
    best_cid = max(perf, key=lambda k: perf[k])
    val = perf[best_cid]
    label = next((c["label"] for c in get_bilim()["classes"] if c["id"] == best_cid), best_cid)
    return (f'<div class="crm-card" style="text-align:center;margin-bottom:1.5rem;padding:1rem 1.25rem;">'
            f'<span style="color:{MUTED};font-size:0.95rem;">Лучший класс по успеваемости</span><br/>'
            f'<span style="font-size:1.35rem;font-weight:800;color:{PRIMARY};">{label}</span> '
            f'<span style="color:{MUTED};">({val}%)</span></div>')

def render_feed_page(*, mega_fonts: bool, show_best_class: bool = False) -> None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if show_best_class:
            st.markdown(_best_class_banner_html(), unsafe_allow_html=True)
        render_news_feed_content(mega_fonts=mega_fonts)
        st.markdown("### 📅 Расписание на сегодня")
        sched = ensure_schedule()
        today = datetime.now().strftime("%A")
        day_map = {"Monday": "ПН", "Tuesday": "ВТ", "Wednesday": "СР", "Thursday": "ЧТ", "Friday": "ПТ", "Saturday": "СБ", "Sunday": "ВС"}
        today_short = day_map.get(today, "ПН")
        today_lessons = [e for e in sched.get("entries", []) if isinstance(e, dict) and e.get("day") == today_short]
        if today_lessons:
            for lesson in today_lessons:
                st.markdown(f"- **{lesson.get('time', '')}** {lesson.get('subject', '')} ({lesson.get('teacher', '')})")
        else:
            st.info("На сегодня уроков не запланировано или расписание не сгенерировано.")

def ensure_schedule() -> dict:
    if st.session_state.admin_schedule is None:
        st.session_state.admin_schedule = generate_schedule_conflict_free(get_bilim())
    return st.session_state.admin_schedule

def render_student_diary() -> None:
    stu = current_student()
    if not stu:
        st.error("Профиль ученика не найден.")
        return
    st.markdown("### 📊 Мой дневник")
    kg = knowledge_graph_status(stu)
    pred = predict_next_soch(stu)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="crm-card"><div style="color:{MUTED};font-size:0.85rem;">Средний балл</div>'
                    f'<div style="font-size:2rem;font-weight:800;color:{PRIMARY}">{pred["avg"]}</div></div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="crm-card"><div style="color:{MUTED};font-size:0.85rem;">Прогноз СОЧ</div>'
                    f'<div style="font-size:2rem;font-weight:800;color:{PRIMARY}">{pred["predicted_soch"]}</div></div>',
                    unsafe_allow_html=True)
    with c3:
        bcls = "risk-on" if kg["risk_flag"] else "risk-off"
        st.markdown(f'<div class="crm-card"><div style="color:{MUTED};font-size:0.85rem;">Граф знаний</div>'
                    f'<span class="risk-badge {bcls}">{kg["status"]}</span></div>',
                    unsafe_allow_html=True)
    st.markdown("#### Расписание")
    sched = ensure_schedule()
    rows = [e for e in sched.get("entries", []) if isinstance(e, dict) and "day" in e and "error" not in e]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("Расписание появится после генерации администратором.")
    st.markdown("#### Оценки по темам и датам")
    st.dataframe(pd.DataFrame(stu["grades_timeline"]), use_container_width=True, hide_index=True)
    st.markdown("#### Предиктивная аналитика (алгоритм)")
    st.markdown(f'<div class="crm-card">'
                f"<p><strong>Вероятность успеха {pred['success_probability_pct']}%.</strong> "
                f"Слабая тема: <em>{pred['weak_topic']}</em>.<br/>"
                f"Рекомендация: посмотри видео — «{pred['recommendation_video']}».</p>"
                f"<p style='color:{MUTED};font-size:0.9rem;'>{pred['rationale']}</p></div>",
                unsafe_allow_html=True)
    att = stu["attendance"]
    st.markdown(f'<div class="crm-card">✅ Присутствий: <strong>{att["present"]}</strong> • '
                f'❌ Пропусков (не уваж.): <strong>{att["absent"]}</strong> • '
                f'⏱ Опозданий: <strong>{att.get("late", 0)}</strong> • '
                f'🤒 Болезнь (дней): <strong>{att.get("sick", 0)}</strong></div>',
                unsafe_allow_html=True)
    st.caption("Отметки посещаемости выставляет классный руководитель в журнале.")

def alaman_bot_brain(prompt: str, stu: dict | None, role: str) -> str:
    p = prompt.lower()
    if role == "teacher":
        if "отчет" in p or "отстаю" in p or "падение" in p:
            anomalies = students_with_anomaly_drop(get_bilim())
            if anomalies:
                report = "📉 **Ученики с аномальным падением успеваемости (разница >20 баллов):**\n"
                for a in anomalies:
                    report += f"- {a.get('student_name', 'Неизвестно')}: было {a.get('prev_avg', 0)} → стало {a.get('curr_avg', 0)} (Δ {a.get('delta', 0)})\n"
                return report
            else:
                return "Хорошие новости! Нет учеников с резким падением успеваемости."
        if "успеваемость" in p or "баллы" in p:
            ranking = students_ranking(get_bilim())
            if ranking:
                top = ranking[:3]
                report = "🏆 **Топ-3 ученика по успеваемости:**\n"
                for i, r in enumerate(top, 1):
                    report += f"{i}. {r.get('name', '')} - средний балл {r.get('avg_score', 0)}\n"
                return report
    if stu:
        grades = stu.get("grades_timeline", [])
        if "балл" in p or "оценки" in p:
            subjects = {}
            for g in grades:
                topic = g.get("topic", "").lower()
                score = g.get("score", 0)
                if topic:
                    if topic not in subjects:
                        subjects[topic] = []
                    subjects[topic].append(score)
            if subjects:
                avg_by_subj = {k: sum(v)/len(v) for k, v in subjects.items()}
                response = "📊 Средние баллы по предметам:\n"
                for subj, avg in avg_by_subj.items():
                    response += f"- {subj.capitalize()}: {avg:.1f}\n"
                return response
            else:
                return "У тебя пока нет оценок по предметам."
        if "математик" in p or "математика" in p:
            math_grades = [g["score"] for g in grades if "математика" in g.get("topic", "").lower()]
            if math_grades:
                avg = sum(math_grades)/len(math_grades)
                return f"Твой средний балл по математике: {avg:.1f}. Последняя оценка: {math_grades[-1]}."
            else:
                return "Нет данных по математике."
        if "физик" in p or "физика" in p:
            phys_grades = [g["score"] for g in grades if "физика" in g.get("topic", "").lower()]
            if phys_grades:
                avg = sum(phys_grades)/len(phys_grades)
                return f"Твой средний балл по физике: {avg:.1f}. Последняя оценка: {phys_grades[-1]}."
            else:
                return "Нет данных по физике."
        if "литература" in p or "литератур" in p:
            lit_grades = [g["score"] for g in grades if "литература" in g.get("topic", "").lower()]
            if lit_grades:
                avg = sum(lit_grades)/len(lit_grades)
                return f"Твой средний балл по литературе: {avg:.1f}. Последняя оценка: {lit_grades[-1]}."
            else:
                return "Нет данных по литературе."
        pred = predict_next_soch(stu)
        if "шанс" in p or "прогноз" in p:
            return f"Мой алгоритм предсказывает вероятность успеха на СОЧ: **{pred['success_probability_pct']}%**. Ты справишься!"
    if "привет" in p or "салем" in p:
        return "Сәлем! Мен Аламанмын — сенің цифрлық тәлімгеріңмін. Саған оқу бойынша қандай көмек керек?"
    if "расписание" in p or "сабак" in p:
        return "Твоё актуальное расписание уже в дневнике. Проверь вкладку 'Мой дневник'!"
    return "Я проанализировал твои данные в BilimClass. Могу рассказать про твои оценки, прогноз на СОЧ или подсказать слабую тему. Что именно тебя интересует?"

def render_alaman_page(role_key: str) -> None:
    stu = current_student()
    st.markdown("### 🤖 AI-ALAMAN • Твой наставник")
    for m in st.session_state.alaman_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    if prompt := st.chat_input("Спроси Аламана..."):
        st.session_state.alaman_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        reply = alaman_bot_brain(prompt, stu, role_key)
        st.session_state.alaman_messages.append({"role": "assistant", "content": reply})
        st.rerun()

@st.dialog("Alaman • чат", width="large")
def alaman_fab_dialog() -> None:
    stu = current_student()
    for m in st.session_state.alaman_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    if p := st.chat_input("Сообщение..."):
        st.session_state.alaman_messages.append({"role": "user", "content": p})
        st.session_state.alaman_messages.append({"role": "assistant", "content": alaman_bot_brain(p, stu, st.session_state.user_role)})
        st.rerun()
    if st.button("Закрыть"):
        st.session_state.fab_chat_open = False
        st.rerun()

def _fab_container():
    try:
        return st.container(key="fab_alaman")
    except TypeError:
        return st.container()

def render_fab_alaman() -> None:
    with _fab_container():
        if st.button("🤖", key="fab_alaman_btn", help="Alaman"):
            st.session_state.fab_chat_open = True
            st.rerun()
    if st.session_state.fab_chat_open:
        alaman_fab_dialog()

def render_admin_schedule() -> None:
    st.markdown("### ⚙️ Изменить расписание")
    st.caption("Сгенерируйте слоты и при необходимости отредактируйте таблицу, затем сохраните — расписание увидят все роли.")
    if st.button("🗓 Сгенерировать расписание", type="primary", use_container_width=True, key="gen_sched"):
        st.session_state.admin_schedule = generate_schedule_conflict_free(get_bilim())
        st.rerun()
    sched = st.session_state.admin_schedule
    if sched:
        rows = [e for e in sched.get("entries", []) if isinstance(e, dict) and "day" in e and "error" not in e]
        err = [e for e in sched.get("entries", []) if isinstance(e, dict) and e.get("error")]
        if rows:
            df = pd.DataFrame(rows)
            edited = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="sched_edit")
            if st.button("💾 Сохранить расписание", type="primary", use_container_width=True, key="save_sched"):
                new_entries = edited.to_dict("records")
                st.session_state.admin_schedule = {
                    **sched,
                    "entries": new_entries + err,
                    "saved_at": datetime.now().isoformat(timespec="seconds"),
                }
                st.success("Расписание сохранено.")
                st.rerun()
        elif err:
            st.warning(f"Не удалось разместить уроков: {len(err)}.")
        else:
            st.info("Нет строк для отображения — сгенерируйте расписание.")
    else:
        st.info("Расписание ещё не создано. Нажмите «Сгенерировать расписание».")

def render_admin_analytics() -> None:
    st.markdown("### 📈 Общая аналитика")
    perf = class_performance_percent(get_bilim())
    for cid, val in perf.items():
        label = next((c["label"] for c in get_bilim()["classes"] if c["id"] == cid), cid)
        pct = min(100, max(0, val))
        st.markdown(f"**{label}** — средний балл **{val}** ({pct}% от максимума)")
        st.progress(pct / 100.0)

def render_admin_news() -> None:
    st.markdown("### 👥 Управление новостями")
    with st.form("pub"):
        title = st.text_input("Заголовок")
        body = st.text_area("Текст")
        img = st.file_uploader("Фото", type=["png", "jpg", "jpeg"])
        vid = st.file_uploader("Видео", type=["mp4", "webm"])
        sub = st.form_submit_button("Опубликовать для всех")
    if sub:
        if not title.strip() or not body.strip():
            st.warning("Заголовок и текст обязательны.")
        else:
            new_news = {
                "id": str(uuid.uuid4()),
                "title": title.strip(),
                "body": body.strip(),
                "published_at": datetime.now().isoformat(timespec="seconds"),
                "image_url": None,
                "video_url": None,
                "image_data": None,
                "video_data": None,
            }
            if img is not None:
                new_news["image_data"] = img.getvalue()
            if vid is not None:
                new_news["video_data"] = vid.getvalue()
            st.session_state.news_items.insert(0, new_news)
            save_news(st.session_state.news_items)
            st.success("Новость опубликована — видна всем ролям на главной.")
            st.rerun()

def render_admin_technical_expander() -> None:
    with st.expander("🔧 Справочники Mock API и технические настройки", expanded=False):
        st.caption("Только для администратора.")
        st.markdown("Для **Alaman** с OpenAI задайте переменную окружения `OPENAI_API_KEY` (иначе — алгоритм из `bilim_engine.py`).")
        st.json({
            "meta": get_bilim()["meta"],
            "teachers": get_bilim()["teachers"],
            "rooms": get_bilim()["rooms"],
            "classes": get_bilim()["classes"],
            "lesson_templates": get_bilim()["lesson_templates"],
        })

def render_teacher_classes() -> None:
    st.markdown("### 📝 Журнал оценок")
    st.caption("Выберите ученика и добавьте новую оценку. Оценки автоматически попадают в дневник ученика.")
    current_user = st.session_state.user_login
    teacher_class = st.session_state.users_db[current_user].get("class_name", "")
    # Динамический список учеников из users_db
    students_in_class = []
    for login, data in st.session_state.users_db.items():
        if data.get("role") == "student" and data.get("class_name") == teacher_class:
            students_in_class.append((login, data["name"], data.get("student_id", login)))
    if not students_in_class:
        st.info("В вашем классе нет учеников.")
        return
    selected_student = st.selectbox("Выберите ученика", students_in_class,
                                    format_func=lambda x: f"{x[1]} (логин: {x[0]})")
    student_login, student_name, student_id = selected_student
    with st.form("add_grade_form"):
        grade_date = st.date_input("Дата оценки", datetime.now())
        topic = st.text_input("Тема урока")
        score = st.number_input("Оценка (балл)", min_value=0, max_value=100, step=1, value=50)
        submitted = st.form_submit_button("Поставить оценку")
        if submitted:
            if not topic.strip():
                st.warning("Введите тему урока")
            else:
                add_grade_to_student(student_id, grade_date.isoformat(), topic.strip(), score)
                st.success(f"Оценка {score} по предмету '{topic}' выставлена {student_name}")
                st.rerun()
    # Показываем последние оценки выбранного ученика
    bilim = get_bilim()
    student_data = get_student_by_id(bilim, student_id)
    if student_data and student_data.get("grades_timeline"):
        st.markdown(f"**Последние оценки {student_name}:**")
        df_grades = pd.DataFrame(student_data["grades_timeline"][-5:])
        st.dataframe(df_grades, use_container_width=True, hide_index=True)

def render_teacher_performance() -> None:
    st.markdown("### 🚨 Успеваемость")
    for s in get_bilim()["students"]:
        tr = student_performance_trend(s)
        bg, fg = BADGE_CSS.get(tr["badge"], ("#f1f5f9", "#334155"))
        if tr.get("prev_avg") is None:
            ls = tr.get("last_score")
            line = f"Пока одна оценка в журнале: {ls}." if ls is not None else "Нет оценок для сравнения."
        else:
            prev_s = tr.get("previous_score")
            if prev_s is not None:
                line = (f"Предыдущая оценка: {prev_s} → последняя: {tr['last_score']} "
                        f"(Δ {tr['delta']:+g}) • периоды: {tr['prev_avg']} → {tr['curr_avg']}")
            else:
                line = f"Периоды: {tr['prev_avg']} → {tr['curr_avg']} (Δ {tr['delta']:+g})"
        st.markdown(f'<div class="crm-card" style="background:{bg};border-color:{fg};">'
                    f"<strong>{s['full_name']}</strong> • {tr['label']}<br/>{line}</div>",
                    unsafe_allow_html=True)
    an = students_with_anomaly_drop(get_bilim())
    st.markdown("#### Аномальное падение успеваемости (разница более 20 баллов)")
    if an:
        st.dataframe(pd.DataFrame(an), use_container_width=True, hide_index=True)
    else:
        st.success("Таких случаев нет.")

def render_parent_child() -> None:
    stu = current_student()
    if not stu:
        st.error("Нет данных о ребёнке.")
        return
    st.markdown("### 📊 Мой ребёнок")
    kg = knowledge_graph_status(stu)
    bcls = "risk-on" if kg["risk_flag"] else "risk-off"
    st.markdown(f'<div class="crm-card">Граф знаний: <span class="risk-badge {bcls}">{kg["status"]}</span></div>',
                unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(stu["grades_timeline"]), use_container_width=True, hide_index=True)
    st.markdown("#### Выжимка за неделю (AI-Summary)")
    st.info(weekly_parent_summary(stu))

def render_chat(role: str) -> None:
    st.markdown("### 💬 Личные сообщения")
    messages = st.session_state.messages
    current_user = st.session_state.user_login
    USERS = st.session_state.users_db
    bilim = get_bilim()
    if role == "student":
        teachers = [u for u, data in USERS.items() if data.get("role") == "teacher"]
        teacher_names = {t: USERS[t]["name"] for t in teachers}
        selected_teacher = st.selectbox("Выберите учителя", teachers, format_func=lambda x: teacher_names.get(x, x))
        filtered = [m for m in messages if (m["sender"] == current_user and m["receiver"] == selected_teacher) or
                    (m["sender"] == selected_teacher and m["receiver"] == current_user)]
        filtered.sort(key=lambda x: x["timestamp"])
        for m in filtered:
            with st.chat_message(m["sender"]):
                st.markdown(f"**{USERS.get(m['sender'], {}).get('name', m['sender'])}**: {m['text']}")
        if prompt := st.chat_input("Напишите учителю..."):
            new_msg = {
                "id": str(uuid.uuid4()),
                "sender": current_user,
                "receiver": selected_teacher,
                "text": prompt,
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.messages.append(new_msg)
            save_messages(st.session_state.messages)
            st.rerun()
    elif role == "teacher":
        teacher_class = USERS[current_user].get("class_name", "")
        students_in_class = []
        for login, data in USERS.items():
            if data.get("role") == "student" and data.get("class_name") == teacher_class:
                students_in_class.append(login)
        if not students_in_class:
            st.info("В вашем классе нет учеников.")
            return
        selected_student = st.selectbox("Выберите ученика", students_in_class,
                                        format_func=lambda x: USERS[x]["name"])
        filtered = [m for m in messages if (m["sender"] == current_user and m["receiver"] == selected_student) or
                    (m["sender"] == selected_student and m["receiver"] == current_user)]
        filtered.sort(key=lambda x: x["timestamp"])
        for m in filtered:
            with st.chat_message(m["sender"]):
                st.markdown(f"**{USERS.get(m['sender'], {}).get('name', m['sender'])}**: {m['text']}")
        if prompt := st.chat_input("Напишите ученику..."):
            new_msg = {
                "id": str(uuid.uuid4()),
                "sender": current_user,
                "receiver": selected_student,
                "text": prompt,
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.messages.append(new_msg)
            save_messages(st.session_state.messages)
            st.rerun()

def main_shell() -> None:
    if "user_role" not in st.session_state or st.session_state.user_role is None:
        st.error("Ошибка сессии. Пожалуйста, войдите заново.")
        logout()
        return
    crm_css()
    role = st.session_state.user_role
    name = st.session_state.display_name
    if role == "student":
        student_hide_sidebar_css()
        row1, row2 = st.columns([4.2, 1])
        with row1:
            nav = st.radio("Навигация", ["🏠 Главная", "📊 Мой дневник", "💬 Чат", "🤖 AI-ALAMAN"],
                           horizontal=True, label_visibility="collapsed", key="student_top_nav")
        with row2:
            st.button("Выйти", type="secondary", use_container_width=True, on_click=logout)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if nav == "🏠 Главная":
            render_feed_page(mega_fonts=True, show_best_class=True)
        elif nav == "📊 Мой дневник":
            st.markdown(f'<div class="crm-header"><h1>📊 Мой дневник</h1><p>{name}</p></div>', unsafe_allow_html=True)
            render_student_diary()
        elif nav == "💬 Чат":
            st.markdown(f'<div class="crm-header"><h1>💬 Чат с учителем</h1><p>{name}</p></div>', unsafe_allow_html=True)
            render_chat("student")
        else:
            st.markdown(f'<div class="crm-header"><h1>🤖 AI-ALAMAN</h1><p>{name}</p></div>', unsafe_allow_html=True)
            render_alaman_page("student")
        render_fab_alaman()
        return
    with st.sidebar:
        st.markdown("## 🎓 Aqbobek Lyceum")
        st.caption(f"{name}")
        st.divider()
        if role == "teacher":
            page = st.radio("Меню", ["🏠 Главная", "📝 Журнал оценок", "🚨 Успеваемость", "💬 Сообщения", "🤖 AI-ALAMAN"],
                            label_visibility="collapsed")
        elif role == "parent":
            page = st.radio("Меню", ["🏠 Главная", "📊 Мой ребенок", "🤖 AI-ALAMAN"],
                            label_visibility="collapsed")
        else:
            page = st.radio("Меню", ["⚙️ Управление расписанием", "📈 Общая аналитика", "👥 Управление новостями"],
                            label_visibility="collapsed")
        st.divider()
        st.button("Выйти", type="secondary", use_container_width=True, on_click=logout)
    st.markdown(f'<div class="crm-header"><h1>🏛️ Aqbobek Lyceum</h1>'
                f"<p>Роль: <strong>{role}</strong> • {name}</p></div>",
                unsafe_allow_html=True)
    if role == "teacher":
        if page == "🏠 Главная":
            render_feed_page(mega_fonts=False, show_best_class=True)
        elif page == "📝 Журнал оценок":
            render_teacher_classes()
        elif page == "🚨 Успеваемость":
            render_teacher_performance()
        elif page == "💬 Сообщения":
            render_chat("teacher")
        else:
            render_alaman_page("teacher")
        render_fab_alaman()
    elif role == "parent":
        if page == "🏠 Главная":
            render_feed_page(mega_fonts=False, show_best_class=True)
        elif page == "📊 Мой ребенок":
            render_parent_child()
        else:
            render_alaman_page("parent")
        render_fab_alaman()
    else:
        if page == "⚙️ Управление расписанием":
            render_admin_schedule()
        elif page == "📈 Общая аналитика":
            render_admin_analytics()
        else:
            render_admin_news()
        render_admin_technical_expander()

def main() -> None:
    st.set_page_config(page_title="Aqbobek Lyceum Portal", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
    init_app_state()
    if not st.session_state.get("logged_in"):
        render_login()
        return
    main_shell()

if __name__ == "__main__":
    main()