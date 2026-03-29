"""
Aqbobek Lyceum Portal — Streamlit CRM: авторизация, роли, BilimClass (mock), Alaman.
"""

from __future__ import annotations

import copy
import uuid
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

USERS: dict[str, dict] = {
    "admin": {"password": "ad123", "role": "admin", "name": "Администратор"},
    "student": {"password": "s123", "role": "student", "name": "Айым К.", "student_id": "stu_002"},
    "teacher": {"password": "t123", "role": "teacher", "name": "Ерлан Сатыбалды"},
    "parent": {"password": "p123", "role": "parent", "name": "Родитель (Айым)", "child_student_id": "stu_002"},
}

BADGE_CSS = {
    "red": ("#fee2e2", "#b91c1c"),
    "green_bright": ("#bbf7d0", "#15803d"),
    "green_salad": ("#ecfccb", "#4d7c0f"),
    "orange": ("#ffedd5", "#c2410c"),
}


def get_bilim() -> dict:
    """Единый источник mock BilimClass — всегда st.session_state['bilim_data']."""
    return st.session_state.bilim_data


def crm_css() -> None:
    st.markdown(
        f"""
        <style>
            html, body, [class*="css"] {{
                font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important;
            }}
            .stApp {{
                background: linear-gradient(135deg, #e8eef7 0%, #f0f4fa 50%, #e4ecf7 100%);
            }}
            .crm-header {{
                background: linear-gradient(90deg, {PRIMARY} 0%, #152a52 100%);
                color: #fff;
                padding: 1.35rem 1.75rem;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(12, 30, 61, 0.22);
                margin-bottom: 1.75rem;
            }}
            .crm-header h1 {{ margin: 0; font-size: 1.6rem; font-weight: 700; }}
            .crm-header p {{ margin: 0.4rem 0 0 0; opacity: 0.9; font-size: 0.95rem; }}
            .crm-card {{
                background: {CARD};
                border-radius: 20px;
                padding: 1.5rem 1.75rem;
                box-shadow: 0 4px 24px rgba(12, 30, 61, 0.08);
                border: 1px solid rgba(12, 30, 61, 0.06);
                margin-bottom: 1.85rem;
            }}
            .feed-wrap {{
                max-width: 560px;
                margin: 0 auto;
            }}
            .feed-card {{
                background: #fff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 6px 28px rgba(12, 30, 61, 0.1);
                margin-bottom: 2rem;
                border: 1px solid rgba(12, 30, 61, 0.07);
            }}
            .feed-card h2 {{
                color: {PRIMARY};
                padding: 1rem 1.25rem 0.25rem;
                margin: 0;
                font-size: 1.35rem;
            }}
            .feed-card .meta {{
                color: {MUTED};
                padding: 0 1.25rem 0.75rem;
                font-size: 0.9rem;
            }}
            .feed-card img, .feed-card video {{
                width: 100%;
                display: block;
                max-height: 420px;
                object-fit: cover;
            }}
            .feed-card .body {{
                padding: 1rem 1.25rem 1.35rem;
                color: #334155;
                line-height: 1.55;
            }}
            .risk-badge {{
                display: inline-block;
                padding: 0.3rem 0.85rem;
                border-radius: 999px;
                font-weight: 600;
                font-size: 0.88rem;
            }}
            .risk-on {{ background: #fee2e2; color: #b91c1c; }}
            .risk-off {{ background: #dcfce7; color: #166534; }}
            div[data-testid="stSidebar"] {{
                background: linear-gradient(180deg, {PRIMARY} 0%, #132447 100%);
            }}
            div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] label {{
                color: #e2e8f0 !important;
            }}
            .login-box {{
                max-width: 420px;
                margin: 3rem auto;
                padding: 2.5rem;
                background: #fff;
                border-radius: 20px;
                box-shadow: 0 16px 48px rgba(12, 30, 61, 0.12);
            }}
            .login-title {{
                text-align: center;
                color: {PRIMARY};
                font-size: 1.75rem;
                font-weight: 800;
                margin-bottom: 1.75rem;
            }}
            .login-shell {{
                min-height: 88vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1rem;
            }}
            div[data-testid="stSidebar"] label span {{
                font-weight: 500;
                letter-spacing: 0.02em;
            }}
            div[data-testid="stSidebar"] .stRadio > div {{
                gap: 0.35rem;
            }}
            div[class*="st-key-fab_alaman"] {{
                position: fixed !important;
                bottom: 24px !important;
                right: 20px !important;
                z-index: 999999 !important;
                width: auto !important;
            }}
            div[class*="st-key-fab_alaman"] button {{
                border-radius: 50% !important;
                width: 58px !important;
                min-width: 58px !important;
                height: 58px !important;
                font-size: 1.45rem !important;
                box-shadow: 0 10px 28px rgba(61, 139, 253, 0.42);
            }}
            .student-mega .feed-card h2 {{
                font-size: clamp(1.75rem, 4vw, 2.35rem) !important;
            }}
            .student-mega .feed-card .body {{
                font-size: clamp(1.1rem, 2.5vw, 1.4rem) !important;
            }}
            .student-mega .feed-card .meta {{
                font-size: 1rem !important;
            }}
            div[data-testid="stDialog"] {{
                border-radius: 20px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def student_hide_sidebar_css() -> None:
    """Главная ученика: полноэкранная лента, боковое меню скрыто (ТЗ)."""
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                visibility: hidden !important;
                min-width: 0 !important;
                width: 0 !important;
            }
            div[data-testid="stSidebarCollapsedControl"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def login_hide_sidebar_css() -> None:
    """Пока не вошли — меню и контент CRM скрыты (ТЗ)."""
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
                min-width: 0 !important;
            }
            div[data-testid="stSidebarCollapsedControl"] { display: none !important; }
            header[data-testid="stHeader"] { background: transparent; }
            .block-container { padding-top: 2rem !important; max-width: 520px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_app_state() -> None:
    """Инициализация данных приложения. Не трогает logged_in, если ключ уже есть."""
    if "bilim_data" not in st.session_state:
        st.session_state.bilim_data = build_initial_mock_bilim()
    if "news_items" not in st.session_state:
        st.session_state.news_items = copy.deepcopy(MOCK_NEWS_SEED)
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


def logout() -> None:
    st.session_state.clear()
    st.rerun()


def current_student() -> dict | None:
    ur = st.session_state.get("user_role")
    if ur == "student":
        sid = USERS[st.session_state.user_login].get("student_id", "stu_002")
        return get_student_by_id(get_bilim(), sid)
    if ur == "parent":
        sid = USERS[st.session_state.user_login].get("child_student_id", "stu_002")
        return get_student_by_id(get_bilim(), sid)
    return None


def render_login() -> None:
    login_hide_sidebar_css()
    crm_css()
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.markdown(
            '<div class="login-shell"><div class="login-box">'
            '<p class="login-title">Aqbobek Lyceum Portal</p>',
            unsafe_allow_html=True,
        )
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
        st.markdown("</div></div>", unsafe_allow_html=True)


def merged_news() -> list[dict]:
    return sort_news_desc(st.session_state.news_items)


PLACEHOLDER_IMG = "https://via.placeholder.com/600x400"


def render_news_feed_content(*, mega_fonts: bool) -> None:
    """Лента публикаций администратора: центральная колонка, свежие сверху."""
    wrap_class = "feed-wrap student-mega" if mega_fonts else "feed-wrap"
    st.markdown(f'<div class="{wrap_class}">', unsafe_allow_html=True)
    for idx, n in enumerate(merged_news()):
        nid = str(n.get("id") or f"news_{idx}")
        vid = (n.get("video_url") or "").strip()
        img = (n.get("image_url") or "").strip()
        media_html = ""
        if vid:
            media_html = f'<video src="{vid}" controls playsinline></video>'
        elif img:
            media_html = f'<img src="{img}" alt="" />'
        else:
            media_html = f'<img src="{PLACEHOLDER_IMG}" alt="" />'
        dt = n.get("published_at", "")[:16].replace("T", " ")
        st.markdown(
            f"""
            <div class="feed-card">
                <h2>{n.get("title", "")}</h2>
                <div class="meta">{dt}</div>
                {media_html}
                <div class="body">{n.get("body", "")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        likes = int(st.session_state.news_likes.get(nid, 0))
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
    return (
        f'<div class="crm-card" style="text-align:center;margin-bottom:1.5rem;padding:1rem 1.25rem;">'
        f'<span style="color:{MUTED};font-size:0.95rem;">Лучший класс по успеваемости</span><br/>'
        f'<span style="font-size:1.35rem;font-weight:800;color:{PRIMARY};">{label}</span> '
        f'<span style="color:{MUTED};">({val}%)</span></div>'
    )


def render_feed_page(*, mega_fonts: bool, show_best_class: bool = False) -> None:
    """st.columns([1, 2, 1]) — лента только в средней колонке."""
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if show_best_class:
            st.markdown(_best_class_banner_html(), unsafe_allow_html=True)
        render_news_feed_content(mega_fonts=mega_fonts)


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
        st.markdown(
            f'<div class="crm-card"><div style="color:{MUTED};font-size:0.85rem;">Средний балл</div>'
            f'<div style="font-size:2rem;font-weight:800;color:{PRIMARY}">{pred["avg"]}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="crm-card"><div style="color:{MUTED};font-size:0.85rem;">Прогноз СОЧ</div>'
            f'<div style="font-size:2rem;font-weight:800;color:{PRIMARY}">{pred["predicted_soch"]}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        bcls = "risk-on" if kg["risk_flag"] else "risk-off"
        st.markdown(
            f'<div class="crm-card"><div style="color:{MUTED};font-size:0.85rem;">Граф знаний</div>'
            f'<span class="risk-badge {bcls}">{kg["status"]}</span></div>',
            unsafe_allow_html=True,
        )

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
    st.markdown(
        f'<div class="crm-card">'
        f"<p><strong>Вероятность успеха {pred['success_probability_pct']}%.</strong> "
        f"Слабая тема: <em>{pred['weak_topic']}</em>.<br/>"
        f"Рекомендация: посмотри видео — «{pred['recommendation_video']}».</p>"
        f"<p style='color:{MUTED};font-size:0.9rem;'>{pred['rationale']}</p></div>",
        unsafe_allow_html=True,
    )

    att = stu["attendance"]
    st.markdown(
        f'<div class="crm-card">✅ Присутствий: <strong>{att["present"]}</strong> · '
        f'❌ Пропусков (не уваж.): <strong>{att["absent"]}</strong> · '
        f'⏱ Опозданий: <strong>{att.get("late", 0)}</strong> · '
        f'🤒 Болезнь (дней): <strong>{att.get("sick", 0)}</strong></div>',
        unsafe_allow_html=True,
    )
    st.caption("Отметки посещаемости выставляет классный руководитель в журнале.")


def render_alaman_page(role_key: str) -> None:
    """Полноэкранный чат Alaman (тот же бот, что и у плавающей кнопки)."""
    stu: dict | None = None
    if role_key in ("student", "parent"):
        stu = current_student()
    name = st.session_state.get("display_name", "Пользователь")
    role = st.session_state.get("user_role", role_key)
    st.markdown("### 🤖 AI-ALAMAN · Alaman")
    st.caption("Предиктивная аналитика по дневнику; при наличии ключа — OpenAI API.")

    if st.session_state.get("user_role") == "teacher":
        tc1, tc2 = st.columns(2)
        with tc1:
            if st.button("📄 Сгенерировать отчёт для директора", key="alaman_dir_rep", use_container_width=True):
                st.session_state.director_report = generate_director_ai_report(get_bilim())
        with tc2:
            if st.button("📊 Рейтинг учеников", key="alaman_rank_btn", use_container_width=True):
                st.session_state.teacher_show_ranking = True
        if st.session_state.director_report:
            st.markdown(st.session_state.director_report)
        if st.session_state.teacher_show_ranking:
            st.dataframe(pd.DataFrame(students_ranking(get_bilim())), use_container_width=True, hide_index=True)
        st.divider()

    if not st.session_state.alaman_messages:
        intro = alaman_opening_message(stu, name, role if isinstance(role, str) else role_key)
        st.session_state.alaman_messages = [{"role": "assistant", "content": intro}]

    for m in st.session_state.alaman_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Напишите Alaman…", key="alaman_page_input"):
        st.session_state.alaman_messages.append({"role": "user", "content": prompt})
        reply = alaman_bot_reply(prompt, student=stu, role=st.session_state.get("user_role", ""), display_name=name)
        st.session_state.alaman_messages.append({"role": "assistant", "content": reply})
        st.rerun()


@st.dialog("Alaman · чат", width="large")
def alaman_fab_dialog() -> None:
    role = st.session_state.get("user_role", "")
    stu: dict | None = current_student() if role in ("student", "parent") else None
    name = st.session_state.get("display_name", "")

    if not st.session_state.alaman_messages:
        intro = alaman_opening_message(stu, name, role if isinstance(role, str) else "")
        st.session_state.alaman_messages = [{"role": "assistant", "content": intro}]

    for m in st.session_state.alaman_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    if p := st.chat_input("Сообщение…", key="alaman_dialog_input"):
        st.session_state.alaman_messages.append({"role": "user", "content": p})
        st.session_state.alaman_messages.append(
            {
                "role": "assistant",
                "content": alaman_bot_reply(p, student=stu, role=role, display_name=name),
            }
        )
        st.rerun()
    if st.button("Закрыть"):
        st.session_state.fab_chat_open = False
        st.rerun()


def _fab_container():
    """Streamlit ≥1.33: key у container; иначе — обычный блок (CSS может не зафиксировать кнопку)."""
    try:
        return st.container(key="fab_alaman")
    except TypeError:
        return st.container()


def render_fab_alaman() -> None:
    """Круглая кнопка в правом нижнем углу — открывает диалог чата Alaman."""
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
            image_url = "https://via.placeholder.com/900x400/3d8bfd/ffffff?text=News"
            video_url = None
            if img is not None:
                st.caption("Демо: файл не хранится на сервере — показана заглушка.")
            if vid is not None:
                st.caption("Демо: видео в ленту — заглушка.")
                video_url = "https://www.w3schools.com/html/mov_bbb.mp4"
            st.session_state.news_items.insert(
                0,
                {
                    "id": str(uuid.uuid4()),
                    "title": title.strip(),
                    "body": body.strip(),
                    "published_at": datetime.now().isoformat(timespec="seconds"),
                    "image_url": None if video_url else image_url,
                    "video_url": video_url,
                },
            )
            st.success("Новость опубликована — видна всем ролям на главной.")
            st.rerun()


def render_admin_technical_expander() -> None:
    """Справочники BilimClass (mock) и технастройки — только у администратора (ТЗ)."""
    with st.expander("🔧 Справочники Mock API и технические настройки", expanded=False):
        st.caption("Только для администратора.")
        st.markdown(
            "Для **Alaman** с OpenAI задайте переменную окружения `OPENAI_API_KEY` "
            "(иначе — алгоритм из `bilim_engine.py`)."
        )
        st.json(
            {
                "meta": get_bilim()["meta"],
                "teachers": get_bilim()["teachers"],
                "rooms": get_bilim()["rooms"],
                "classes": get_bilim()["classes"],
                "lesson_templates": get_bilim()["lesson_templates"],
            }
        )


def render_teacher_classes() -> None:
    st.markdown("### 📝 Мои классы")
    st.caption("Изменения сохраняются в демо-журнале и сразу видны ученику и родителю в «Мой дневник» / «Мой ребёнок».")
    bilim = get_bilim()
    rows = []
    for s in bilim["students"]:
        g = s.get("grades_timeline", [])
        last = g[-1] if g else {}
        att = s.get("attendance", {})
        rows.append(
            {
                "student_id": s["id"],
                "Ученик": s["full_name"],
                "Класс": s["class_id"],
                "Последняя оценка": int(last.get("score", 0)) if last else 0,
                "Тема (последняя)": str(last.get("topic", "")),
                "Опозданий": int(att.get("late", 0)),
                "Пропусков": int(att.get("absent", 0)),
                "Болезнь (дней)": int(att.get("sick", 0)),
            }
        )
    df = pd.DataFrame(rows)
    edited = st.data_editor(
        df,
        column_config={
            "student_id": st.column_config.TextColumn("ID", disabled=True, width="small"),
            "Ученик": st.column_config.TextColumn(disabled=True),
            "Класс": st.column_config.TextColumn(disabled=True),
            "Последняя оценка": st.column_config.NumberColumn(min_value=0, max_value=100, step=1),
            "Тема (последняя)": st.column_config.TextColumn(),
            "Опозданий": st.column_config.NumberColumn(min_value=0, step=1),
            "Пропусков": st.column_config.NumberColumn(min_value=0, step=1),
            "Болезнь (дней)": st.column_config.NumberColumn(min_value=0, step=1),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="teacher_journal_editor",
    )
    if st.button("💾 Сохранить в журнал", type="primary", key="save_teacher_journal"):
        for _, row in edited.iterrows():
            sid = row["student_id"]
            for stu in bilim["students"]:
                if stu["id"] != sid:
                    continue
                if stu.get("grades_timeline"):
                    stu["grades_timeline"][-1]["score"] = int(row["Последняя оценка"])
                    stu["grades_timeline"][-1]["topic"] = str(row["Тема (последняя)"])
                if "attendance" not in stu:
                    stu["attendance"] = {}
                stu["attendance"]["late"] = int(row["Опозданий"])
                stu["attendance"]["absent"] = int(row["Пропусков"])
                stu["attendance"]["sick"] = int(row["Болезнь (дней)"])
                break
        st.session_state.bilim_data = bilim
        st.success("Журнал обновлён — данные синхронизированы.")
        st.rerun()


def render_teacher_performance() -> None:
    st.markdown("### 🚨 Успеваемость")
    for s in get_bilim()["students"]:
        tr = student_performance_trend(s)
        bg, fg = BADGE_CSS.get(tr["badge"], ("#f1f5f9", "#334155"))
        if tr.get("prev_avg") is None:
            ls = tr.get("last_score")
            line = (
                f"Пока одна оценка в журнале: {ls}."
                if ls is not None
                else "Нет оценок для сравнения."
            )
        else:
            prev_s = tr.get("previous_score")
            if prev_s is not None:
                line = (
                    f"Предыдущая оценка: {prev_s} → последняя: {tr['last_score']} "
                    f"(Δ {tr['delta']:+g}) · периоды: {tr['prev_avg']} → {tr['curr_avg']}"
                )
            else:
                line = f"Периоды: {tr['prev_avg']} → {tr['curr_avg']} (Δ {tr['delta']:+g})"
        st.markdown(
            f'<div class="crm-card" style="background:{bg};border-color:{fg};">'
            f"<strong>{s['full_name']}</strong> · {tr['label']}<br/>{line}"
            f"</div>",
            unsafe_allow_html=True,
        )

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
    st.markdown(
        f'<div class="crm-card">Граф знаний: <span class="risk-badge {bcls}">{kg["status"]}</span></div>',
        unsafe_allow_html=True,
    )
    st.dataframe(pd.DataFrame(stu["grades_timeline"]), use_container_width=True, hide_index=True)
    st.markdown("#### Выжимка за неделю (AI-Summary)")
    st.info(weekly_parent_summary(stu))


def main_shell() -> None:
    init_app_state()
    crm_css()
    role = st.session_state.user_role
    name = st.session_state.display_name

    if role == "student":
        student_hide_sidebar_css()
        row1, row2 = st.columns([4.2, 1])
        with row1:
            st.radio(
                "Навигация",
                ["🏠 Главная", "📊 Мой дневник", "🤖 AI-ALAMAN"],
                horizontal=True,
                label_visibility="collapsed",
                key="student_top_nav",
            )
        with row2:
            st.button("Выйти", type="secondary", use_container_width=True, on_click=logout)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        sel = st.session_state.get("student_top_nav", "🏠 Главная")
        if sel == "🏠 Главная":
            render_feed_page(mega_fonts=True, show_best_class=True)
        elif sel == "📊 Мой дневник":
            st.markdown(
                f'<div class="crm-header"><h1>📊 Мой дневник</h1><p>{name}</p></div>',
                unsafe_allow_html=True,
            )
            render_student_diary()
        else:
            st.markdown(
                f'<div class="crm-header"><h1>🤖 AI-ALAMAN</h1><p>{name}</p></div>',
                unsafe_allow_html=True,
            )
            render_alaman_page("student")
        render_fab_alaman()
        return

    with st.sidebar:
        st.markdown("## 🎓 Aqbobek Lyceum")
        st.caption(f"{name}")
        st.divider()

        if role == "teacher":
            page = st.radio(
                "Меню",
                ["🏠 Главная", "📝 Мои классы", "🚨 Успеваемость", "🤖 AI-ALAMAN"],
                label_visibility="collapsed",
            )
        elif role == "parent":
            page = st.radio(
                "Меню",
                ["🏠 Главная", "📊 Мой ребенок", "🤖 AI-ALAMAN"],
                label_visibility="collapsed",
            )
        else:
            page = st.radio(
                "Меню",
                ["⚙️ Управление расписанием", "📈 Общая аналитика", "👥 Управление новостями"],
                label_visibility="collapsed",
            )

        st.divider()
        st.button("Выйти", type="secondary", use_container_width=True, on_click=logout)

    st.markdown(
        f'<div class="crm-header"><h1>🏛️ Aqbobek Lyceum</h1>'
        f"<p>Роль: <strong>{role}</strong> · {name}</p></div>",
        unsafe_allow_html=True,
    )

    if role == "teacher":
        if page == "🏠 Главная":
            render_feed_page(mega_fonts=False, show_best_class=True)
        elif page == "📝 Мои классы":
            render_teacher_classes()
        elif page == "🚨 Успеваемость":
            render_teacher_performance()
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
    st.set_page_config(
        page_title="Aqbobek Lyceum Portal",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_app_state()

    if not st.session_state.get("logged_in"):
        render_login()
        return

    main_shell()


if __name__ == "__main__":
    main()
