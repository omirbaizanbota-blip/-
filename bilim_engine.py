"""
Mock BilimClass-подобные данные и бизнес-логика: граф знаний, СОЧ, расписание, ранние предупреждения.
"""

from __future__ import annotations

import copy
import math
import random
from datetime import date, timedelta
from typing import Any

# --- JSON-подобная структура (имитация BilimClass API) ---
# Ученики: grades_timeline — оценки по темам и датам; attendance — посещаемость;
# lesson_topics_log — темы уроков по датам. Связь с классами и учителями — через class_id / teachers.
# Шаблон без учеников — полный снимок даёт build_initial_mock_bilim() (для st.session_state в app.py).
INITIAL_BILIM_TEMPLATE: dict[str, Any] = {
    "meta": {"school": "Aqbobek Lyceum", "year": "2025/2026"},
    "teachers": [
        {"id": "t1", "name": "Айгуль Нурланова", "subjects": ["Физика", "Астрономия"]},
        {"id": "t2", "name": "Ерлан Сатыбалды", "subjects": ["Математика", "Информатика"]},
        {"id": "t3", "name": "Сара Омирова", "subjects": ["Английский"]},
        {"id": "t4", "name": "Данияр Беков", "subjects": ["История", "Обществознание"]},
        {"id": "t5", "name": "Алма Жумабаева", "subjects": ["Химия", "Физика"]},
        {"id": "t6", "name": "Нурлан Касымов", "subjects": ["Математика"]},
    ],
    "rooms": [
        {"id": "r1", "name": "Каб. 201 (физика)", "capacity": 24},
        {"id": "r2", "name": "Каб. 305 (инф.)", "capacity": 20},
        {"id": "r3", "name": "Каб. 112 (языки)", "capacity": 18},
        {"id": "r4", "name": "Актовый зал", "capacity": 80},
    ],
    "classes": [
        {"id": "c10a", "label": "10А", "homeroom_teacher_id": "t2"},
        {"id": "c11b", "label": "11Б", "homeroom_teacher_id": "t1"},
    ],
    "lesson_templates": [
        {"class_id": "c10a", "subject": "Физика", "hours_per_week": 3},
        {"class_id": "c10a", "subject": "Математика", "hours_per_week": 4},
        {"class_id": "c10a", "subject": "Английский", "hours_per_week": 2},
        {"class_id": "c11b", "subject": "Физика", "hours_per_week": 3},
        {"class_id": "c11b", "subject": "История", "hours_per_week": 2},
        {"class_id": "c11b", "subject": "Математика", "hours_per_week": 4},
    ],
    "students": [],
}


def build_initial_mock_bilim() -> dict[str, Any]:
    """Единая точка создания mock BilimClass — копируйте в st.session_state['bilim_data']."""
    data = copy.deepcopy(INITIAL_BILIM_TEMPLATE)
    data["students"] = _build_demo_students()
    return data

# Видео-рекомендации по темам (демо)
TOPIC_VIDEOS: dict[str, str] = {
    "Квантовая физика": "MIT OCW — Introduction to Quantum Mechanics (лекция 1)",
    "Механика": "Khan Academy — Newton's Laws (плейлист)",
    "Термодинамика": "Veritasium — Entropy explained",
    "Дифференциальные уравнения": "3Blue1Brown — Differential equations",
    "Программирование": "freeCodeCamp — Python Data Structures",
    "История Казахстана": "Qazaq Academy — Абай и реформы",
    "Английский": "BBC Learning English — Grammar reference",
    "default": "YouTube Education — повторение по конспекту лицея",
}


def _build_demo_students() -> list[dict[str, Any]]:
    rng = random.Random(7)
    topics_phys = [
        ("Механика", 72),
        ("Термодинамика", 68),
        ("Квантовая физика", 55),
    ]
    topics_math = [
        ("Алгебра", 88),
        ("Геометрия", 82),
        ("Дифференциальные уравнения", 74),
    ]
    students: list[dict[str, Any]] = []
    base = date(2026, 1, 6)
    for i, (sid, name, class_id, topic_rows, att) in enumerate(
        [
            (
                "stu_001",
                "Алихан Е.",
                "c10a",
                [
                    *[(t, base + timedelta(days=j * 7), s) for j, (t, s) in enumerate(topics_phys)],
                    *[(t, base + timedelta(days=21 + j * 7), s) for j, (t, s) in enumerate(topics_math)],
                ],
                {"present": 48, "absent": 2, "late": 1, "sick": 0},
            ),
            (
                "stu_002",
                "Айым К.",
                "c10a",
                [
                    ("Механика", base, 62),
                    ("Термодинамика", base + timedelta(days=7), 58),
                    ("Квантовая физика", base + timedelta(days=14), 52),
                    ("Алгебра", base + timedelta(days=28), 90),
                ],
                {"present": 44, "absent": 3, "late": 2, "sick": 2},
            ),
            (
                "stu_003",
                "Данияр М.",
                "c11b",
                [
                    ("История Казахстана", base, 85),
                    ("Алгебра", base + timedelta(days=5), 88),
                    ("Мировая история", base + timedelta(days=10), 40),
                    ("Геометрия", base + timedelta(days=14), 92),
                    ("Физика", base + timedelta(days=21), 68),
                ],
                {"present": 50, "absent": 0, "late": 0, "sick": 0},
            ),
        ]
    ):
        grades = []
        for topic, d, score in topic_rows:
            grades.append(
                {
                    "topic": topic,
                    "date": d.isoformat(),
                    "score": score,
                    "type": "СОЧ" if "Квантов" in topic or i == 1 else "текущая",
                }
            )
        students.append(
            {
                "id": sid,
                "full_name": name,
                "class_id": class_id,
                "grades_timeline": sorted(grades, key=lambda x: x["date"]),
                "attendance": att,
                "lesson_topics_log": [
                    {"date": (base + timedelta(days=k)).isoformat(), "theme": f"Урок {k + 1}: тема {k % 3 + 1}"}
                    for k in range(12)
                ],
            }
        )
    return students


def knowledge_graph_status(student: dict[str, Any]) -> dict[str, Any]:
    """
    Граф знаний: если по трём темам подряд оценки < 70 — статус «В зоне риска».
    """
    timeline = sorted(student.get("grades_timeline", []), key=lambda x: x["date"])
    risk = False
    window: list[dict[str, Any]] = []
    for g in timeline:
        window.append(g)
        if len(window) > 3:
            window.pop(0)
        if len(window) == 3 and all(w["score"] < 70 for w in window):
            risk = True
            break
    topics_chain = [g["topic"] for g in timeline[-3:]] if len(timeline) >= 3 else [g["topic"] for g in timeline]
    return {
        "student_id": student["id"],
        "status": "В зоне риска" if risk else "Норма",
        "last_three_topics": topics_chain,
        "risk_flag": risk,
    }


def _linear_trend(scores: list[float]) -> float:
    n = len(scores)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2.0
    mean_y = sum(scores) / n
    num = sum((i - mean_x) * (scores[i] - mean_y) for i in range(n))
    den = sum((i - mean_x) ** 2 for i in range(n)) or 1.0
    return num / den


def predict_next_soch(student: dict[str, Any]) -> dict[str, Any]:
    """
    Предиктивная аналитика: средний балл, прогноз следующей СОЧ, слабая тема, рекомендация.
    """
    grades = student.get("grades_timeline", [])
    if not grades:
        return {
            "avg": 0.0,
            "predicted_soch": 0.0,
            "success_probability_pct": 0,
            "weak_topic": "—",
            "recommendation_video": TOPIC_VIDEOS["default"],
            "rationale": "Недостаточно оценок для прогноза.",
        }
    scores = [float(g["score"]) for g in grades]
    topics = [g["topic"] for g in grades]
    avg = sum(scores) / len(scores)
    trend = _linear_trend(scores)
    # прогноз следующей контрольной (СОЧ): экспоненциальное сглаживание + тренд
    last = scores[-1]
    predicted = max(1.0, min(100.0, 0.6 * last + 0.25 * avg + 0.15 * (last + trend * 2)))
    # вероятность «успеха» (≥70) как сигмоида от отклонения от порога
    z = (predicted - 70.0) / 12.0
    prob = int(round(100.0 / (1.0 + math.exp(-z))))
    prob = max(5, min(95, prob))
    weak_idx = min(range(len(scores)), key=lambda i: scores[i])
    weak_topic = topics[weak_idx]
    video = TOPIC_VIDEOS.get(weak_topic, TOPIC_VIDEOS["default"])
    return {
        "avg": round(avg, 1),
        "predicted_soch": round(predicted, 1),
        "success_probability_pct": prob,
        "weak_topic": weak_topic,
        "recommendation_video": video,
        "rationale": f"Тренд по последним оценкам: {trend:+.2f} балла/шаг; последняя оценка {last:.0f}.",
    }


def _teacher_for_subject(subject: str, teachers: list[dict[str, Any]]) -> str | None:
    for t in teachers:
        if subject in t.get("subjects", []):
            return t["id"]
    return None


def generate_schedule_conflict_free(bilim: dict[str, Any]) -> dict[str, Any]:
    """
    Упрощённое расписание: слоты (день, урок), без конфликта «один учитель — два кабинета».
    """
    data = bilim
    teachers = data["teachers"]
    rooms = data["rooms"]
    templates = data["lesson_templates"]
    classes = {c["id"]: c for c in data["classes"]}

    days = ["Пн", "Вт", "Ср", "Чт", "Пт"]
    periods = [1, 2, 3, 4, 5, 6]
    slots: list[tuple[str, int]] = [(d, p) for d in days for p in periods]

    lessons_flat: list[dict[str, Any]] = []
    for lt in templates:
        subj = lt["subject"]
        tid = _teacher_for_subject(subj, teachers)
        if not tid:
            continue
        for _ in range(lt["hours_per_week"]):
            lessons_flat.append(
                {
                    "class_id": lt["class_id"],
                    "class_label": classes[lt["class_id"]]["label"],
                    "subject": subj,
                    "teacher_id": tid,
                }
            )

    rng = random.Random(42)
    rng.shuffle(lessons_flat)
    rng.shuffle(slots)

    schedule: list[dict[str, Any]] = []
    used_teacher_slot: set[tuple[str, str, int]] = set()
    used_room_slot: set[tuple[str, str, int]] = set()

    for lesson in lessons_flat:
        placed = False
        for (day, period) in slots:
            for room in rooms:
                tid = lesson["teacher_id"]
                ts = (tid, day, period)
                rs = (room["id"], day, period)
                if ts in used_teacher_slot or rs in used_room_slot:
                    continue
                used_teacher_slot.add(ts)
                used_room_slot.add(rs)
                schedule.append(
                    {
                        "day": day,
                        "period": period,
                        "room_id": room["id"],
                        "room_name": room["name"],
                        "teacher_id": tid,
                        "teacher_name": next(t["name"] for t in teachers if t["id"] == tid),
                        "class_label": lesson["class_label"],
                        "subject": lesson["subject"],
                    }
                )
                placed = True
                break
            if placed:
                break
        if not placed:
            schedule.append({**lesson, "error": "Не удалось разместить без конфликта"})

    return {"slots_defined": len(slots), "entries": schedule, "generated_at": date.today().isoformat()}


def apply_teacher_sick(
    schedule_state: dict[str, Any],
    sick_teacher_id: str,
    bilim: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """
    Замена больного учителя на свободного с тем же предметом; лог событий.
    """
    data = bilim
    teachers = data["teachers"]
    sick = next((t for t in teachers if t["id"] == sick_teacher_id), None)
    if not sick:
        return schedule_state, ["Учитель не найден."]

    entries = copy.deepcopy(schedule_state.get("entries", []))
    log: list[str] = []
    for row in entries:
        if not isinstance(row, dict) or row.get("teacher_id") != sick_teacher_id:
            continue
        subj = row.get("subject")
        day, period = row.get("day"), row.get("period")
        candidates = [
            t
            for t in teachers
            if t["id"] != sick_teacher_id and subj in t.get("subjects", [])
        ]
        replacement = None
        for t in candidates:
            conflict = any(
                e.get("teacher_id") == t["id"] and e.get("day") == day and e.get("period") == period
                for e in entries
                if isinstance(e, dict) and "teacher_id" in e
            )
            if not conflict:
                replacement = t
                break
        if replacement:
            row["teacher_id"] = replacement["id"]
            row["teacher_name"] = replacement["name"]
            row["replacement_note"] = f"Замена: {sick['name']} → {replacement['name']}"
            log.append(f"{day} п.{period}: {subj} — замена выполнена.")
        else:
            row["replacement_note"] = "Нет свободного учителя на этот слот"
            log.append(f"{day} п.{period}: {subj} — замена невозможна.")

    new_state = {**schedule_state, "entries": entries, "sick_teacher_applied": sick_teacher_id}
    return new_state, log


def students_with_anomaly_drop(bilim: dict[str, Any], threshold: float = 20.0) -> list[dict[str, Any]]:
    """Аномальное падение: разница между текущей и предыдущей оценкой > threshold."""
    data = bilim
    out: list[dict[str, Any]] = []
    for s in data.get("students", []):
        g = sorted(s.get("grades_timeline", []), key=lambda x: x["date"])
        if len(g) < 2:
            continue
        prev, cur = g[-2]["score"], g[-1]["score"]
        drop = float(prev) - float(cur)
        if drop > threshold:
            out.append(
                {
                    "student_id": s["id"],
                    "name": s["full_name"],
                    "class_id": s["class_id"],
                    "previous_score": prev,
                    "current_score": cur,
                    "drop": round(drop, 1),
                    "topics": f"{g[-2]['topic']} → {g[-1]['topic']}",
                }
            )
    return out


def generate_director_ai_report(bilim: dict[str, Any]) -> str:
    """Сводный «ИИ»-отчёт для директора (эвристика на данных, без внешнего API)."""
    data = bilim
    lines: list[str] = []
    lines.append("## Отчёт для директора (Aqbobek Lyceum)")
    lines.append("")
    at_risk = []
    for s in data["students"]:
        kg = knowledge_graph_status(s)
        if kg["risk_flag"]:
            at_risk.append(s["full_name"])
    lines.append(f"- **Ученики в зоне риска (граф знаний):** {len(at_risk)} — {', '.join(at_risk) or 'нет'}.")
    anomalies = students_with_anomaly_drop(data)
    lines.append(f"- **Аномальные просадки:** {len(anomalies)} случаев.")
    for a in anomalies[:5]:
        lines.append(
            f"  - {a['name']}: падение на {a['drop']} баллов ({a['topics']})."
        )
    lines.append("")
    lines.append("**Рекомендации:** усилить наставничество по физике для группы риска; провести встречу с кураторами классов 10А.")
    return "\n".join(lines)


def top_students_day(bilim: dict[str, Any], n: int = 3) -> list[tuple[str, float]]:
    """Топ учеников дня по среднему баллу (демо)."""
    data = bilim
    ranked: list[tuple[str, float]] = []
    for s in data["students"]:
        g = s.get("grades_timeline", [])
        if not g:
            continue
        avg = sum(x["score"] for x in g) / len(g)
        ranked.append((s["full_name"], round(avg, 1)))
    ranked.sort(key=lambda x: -x[1])
    return ranked[:n]


def schedule_changes_summary(schedule_state: dict[str, Any] | None) -> str:
    if not schedule_state:
        return "Замен в расписании пока не было."
    notes = [
        e.get("replacement_note", "")
        for e in schedule_state.get("entries", [])
        if isinstance(e, dict) and e.get("replacement_note")
    ]
    if not notes:
        return "Актуальных замен нет."
    return " | ".join(n for n in notes if n)


# --- Лента новостей (seed) + утилиты ---

MOCK_NEWS_SEED: list[dict[str, Any]] = [
    {
        "id": "n1",
        "title": "Добро пожаловать в портал Aqbobek Lyceum",
        "body": "Здесь расписание, оценки и новости лицея в одном окне.",
        "published_at": "2026-03-28T10:00:00",
        "image_url": "https://via.placeholder.com/900x400/3d8bfd/ffffff?text=Aqbobek+Lyceum",
        "video_url": None,
    },
    {
        "id": "n2",
        "title": "Неделя STEM",
        "body": "Мастер-классы по робототехнике и анализу данных — регистрация открыта.",
        "published_at": "2026-03-25T14:30:00",
        "image_url": "https://via.placeholder.com/900x400/0c1e3d/ffffff?text=STEM",
        "video_url": None,
    },
]


def get_student_by_id(bilim: dict[str, Any], student_id: str) -> dict[str, Any] | None:
    for s in bilim.get("students", []):
        if s.get("id") == student_id:
            return s
    return None


def sort_news_desc(news: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(news, key=lambda x: x.get("published_at", ""), reverse=True)


def class_performance_percent(bilim: dict[str, Any]) -> dict[str, float]:
    """Успеваемость класса в % (средний балл как доля от 100)."""
    data = bilim
    out: dict[str, float] = {}
    for c in data.get("classes", []):
        cid = c["id"]
        studs = [s for s in data.get("students", []) if s.get("class_id") == cid]
        if not studs:
            out[cid] = 0.0
            continue
        avgs: list[float] = []
        for s in studs:
            g = s.get("grades_timeline", [])
            if g:
                avgs.append(sum(float(x["score"]) for x in g) / len(g))
        out[cid] = round(sum(avgs) / len(avgs), 1) if avgs else 0.0
    return out


def weekly_parent_summary(student: dict[str, Any]) -> str:
    """Выжимка за неделю (эвристика без внешнего API)."""
    g = sorted(student.get("grades_timeline", []), key=lambda x: x["date"])
    if not g:
        return "Пока недостаточно оценок для выжимки."
    by_topic: dict[str, list[float]] = {}
    for x in g:
        t = x["topic"]
        by_topic.setdefault(t, []).append(float(x["score"]))
    topic_avg = {t: sum(v) / len(v) for t, v in by_topic.items()}
    best = max(topic_avg, key=topic_avg.get)
    worst = min(topic_avg, key=topic_avg.get)
    return (
        f"Ваш ребенок молодец в «{best}», "
        f"но нужно подтянуть «{worst}»."
    )


def student_performance_trend(student: dict[str, Any]) -> dict[str, Any]:
    """
    Сравнение последней оценки с предыдущей (как требует панель учителя).
    Цвет: рост — ярко-зелёный; без изменений — салатовый; лёгкое падение — оранжевый;
    оценка «ниже 2» (≤2 балла или <20 на 100-балльной шкале) — красный.
    """
    g = sorted(student.get("grades_timeline", []), key=lambda x: x["date"])
    if len(g) < 2:
        return {
            "prev_avg": None,
            "curr_avg": None,
            "delta": 0.0,
            "badge": "green_salad",
            "label": "Недостаточно данных",
            "last_score": float(g[-1]["score"]) if g else None,
        }
    prev = float(g[-2]["score"])
    curr = float(g[-1]["score"])
    delta = curr - prev
    # Периодные средние (для отображения «было / стало»)
    mid = max(1, len(g) // 2)
    prev_scores = [float(x["score"]) for x in g[:mid]]
    curr_scores = [float(x["score"]) for x in g[mid:]]
    prev_avg = sum(prev_scores) / len(prev_scores)
    curr_avg = sum(curr_scores) / len(curr_scores)

    if curr <= 2 or curr < 20:
        badge = "red"
        label = "Критически низкая оценка (зона «двойки»)"
    elif delta > 3:
        badge = "green_bright"
        label = "Оценки выросли по сравнению с прошлой"
    elif abs(delta) <= 2:
        badge = "green_salad"
        label = "Стабильно, как в прошлый раз"
    elif delta < -3:
        badge = "orange"
        label = "Небольшое снижение"
    else:
        badge = "orange"
        label = "Требует внимания"

    return {
        "previous_score": round(prev, 1),
        "prev_avg": round(prev_avg, 1),
        "curr_avg": round(curr_avg, 1),
        "delta": round(delta, 1),
        "badge": badge,
        "label": label,
        "last_score": curr,
    }


def students_ranking(bilim: dict[str, Any]) -> list[dict[str, Any]]:
    """Рейтинг учеников по среднему баллу."""
    data = bilim
    rows: list[dict[str, Any]] = []
    for s in data.get("students", []):
        g = s.get("grades_timeline", [])
        if not g:
            continue
        avg = sum(float(x["score"]) for x in g) / len(g)
        rows.append({"id": s["id"], "name": s["full_name"], "class_id": s["class_id"], "avg": round(avg, 1)})
    rows.sort(key=lambda x: -x["avg"])
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def alaman_bot_reply(
    user_message: str,
    *,
    student: dict[str, Any] | None,
    role: str,
    display_name: str,
) -> str:
    """
    Alaman: предиктивная логика + опционально OpenAI (если задан OPENAI_API_KEY).
    """
    import os

    pred_text = ""
    if student:
        pred = predict_next_soch(student)
        pred_text = (
            f"[Аналитика] Средний балл {pred['avg']}, прогноз СОЧ {pred['predicted_soch']}, "
            f"вероятность успеха {pred['success_probability_pct']}%, слабая тема: {pred['weak_topic']}. "
            f"Рекомендация: {pred['recommendation_video']}."
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            sys_content = (
                "Ты — Alaman, ИИ-наставник Aqbobek Lyceum. Отвечай кратко на русском. "
                "Используй данные об успеваемости, если они даны. " + pred_text
            )
            messages = [
                {"role": "system", "content": sys_content},
                {"role": "user", "content": f"Роль пользователя: {role}. Имя: {display_name}. Запрос: {user_message}"},
            ]
            r = client.chat.completions.create(model="gpt-4o-mini", messages=messages, max_tokens=500)
            return (r.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            return f"OpenAI недоступен ({exc}). Локальный ответ: {pred_text or 'Задайте вопрос про оценки.'}"

    # Локальный алгоритм без API
    um = user_message.lower()
    if student:
        pred = predict_next_soch(student)
        kg = knowledge_graph_status(student)
        if kg["risk_flag"] and "совет" not in um and len(user_message) < 80:
            return (
                f"Привет, {display_name}! По графу знаний: {kg['status']}. "
                f"Вероятность успеха на следующей СОЧ — {pred['success_probability_pct']}%. "
                f"Слабая тема: {pred['weak_topic']}. Рекомендация: посмотри видео «{pred['recommendation_video']}»."
            )
    if any(w in um for w in ("прогноз", "соц", "соч", "предсказ")) and student:
        pred = predict_next_soch(student)
        return (
            f"Вероятность успеха {pred['success_probability_pct']}%. "
            f"Слабая тема: {pred['weak_topic']}. Рекомендация: посмотри видео «{pred['recommendation_video']}»."
        )
    return (
        f"Alaman: я анализирую BilimClass-данные. {pred_text} "
        f"Спросите про прогноз СОЧ или слабые темы."
    )


def alaman_opening_message(
    student: dict[str, Any] | None,
    display_name: str,
    user_role: str,
) -> str:
    """
    Первое сообщение Alaman: привет по имени, анализ дневника; при слабых баллах —
    сразу акцент на вероятность успеха, слабую тему и рекомендацию (предиктивная логика).
    """
    role_hint = ""
    if user_role == "teacher":
        role_hint = " Спросите об успеваемости классов, рейтинге или отчёте для директора."
    if not student:
        return (
            f"Привет, {display_name}! Я **Alaman** — наставник Aqbobek Lyceum "
            f"(алгоритм предиктивной аналитики + опционально OpenAI API).{role_hint}"
        )
    pred = predict_next_soch(student)
    kg = knowledge_graph_status(student)
    weak_line = (
        f'Вероятность успеха: **{pred["success_probability_pct"]}%**. '
        f'Слабая тема: **«{pred["weak_topic"]}»**. '
        f'Рекомендация: посмотри видео «{pred["recommendation_video"]}».'
    )
    if pred["avg"] < 70 or kg["risk_flag"]:
        return (
            f"Привет, {display_name}! Я **Alaman**. По твоему дневнику средний балл **{pred['avg']}** — "
            f"есть зона внимания. Прогноз следующей **СОЧ — {pred['predicted_soch']}**; "
            f"граф знаний: **{kg['status']}**. {weak_line}"
        )
    return (
        f"Привет, {display_name}! Я **Alaman**. Средний балл **{pred['avg']}**, "
        f"прогноз **СОЧ — {pred['predicted_soch']}**, граф знаний: **{kg['status']}**. {weak_line}"
    )


def ai_tutor_proactive_greeting(student: dict[str, Any], display_name: str) -> str | None:
    """Если баллы низкие — первым сообщением совет (совместимость со старым кодом)."""
    pred = predict_next_soch(student)
    if pred["avg"] < 70 or knowledge_graph_status(student)["risk_flag"]:
        return (
            f"{display_name}, вижу напряжённый участок успеваемости (средний {pred['avg']}). "
            f"Начните с темы «{pred['weak_topic']}»: {pred['recommendation_video']}."
        )
    return None
