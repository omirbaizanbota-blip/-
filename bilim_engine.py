import pandas as pd
import random

def build_initial_mock_bilim():
    return {
        "students": [
            {
                "id": "stu_001", "full_name": "Айым К.", "class_id": "11A",
                "grades_timeline": [
                    {"topic": "Math", "score": 85, "date": "2026-03-10"},
                    {"topic": "Math", "score": 92, "date": "2026-03-15"},
                    {"topic": "Physics", "score": 88, "date": "2026-03-18"}
                ],
                "attendance": {"present": 95, "absent": 2, "late": 1}
            },
            {
                "id": "stu_002", "full_name": "Арман И.", "class_id": "11A",
                "grades_timeline": [
                    {"topic": "Math", "score": 55, "date": "2026-03-10"},
                    {"topic": "Math", "score": 48, "date": "2026-03-15"}
                ],
                "attendance": {"present": 70, "absent": 10, "late": 5}
            }
        ],
        "news": [
            {"id": 1, "title": "Наурыз мейрамы!", "body": "Мектебімізде мерекелік іс-шара өтеді.", "date": "2026-03-20"}
        ]
    }

def get_alaman_ai_reply(prompt, user_name, role, bilim):
    p = prompt.lower()
    # Іздеу логикасы: Кім туралы сұрап жатыр?
    target_stu = None
    for s in bilim["students"]:
        if s["full_name"].lower() in p or (role == "student" and user_name in s["full_name"]):
            target_stu = s
            break

    if "баға" in p or "grade" in p or "бал" in p:
        if not target_stu: return "Кімнің бағасын білгіңіз келеді? Оқушының атын жазыңыз."
        grades = [g["score"] for g in target_stu["grades_timeline"]]
        avg = sum(grades)/len(grades) if grades else 0
        status = "✅ Тұрақты" if avg > 70 else "⚠️ Қауіпті аймақ (Risk)"
        return f"**{target_stu['full_name']}** аналитикасы:\n- Орташа балл: {avg:.1f}\n- Күйі: {status}\n- Прогноз: Келесі СОЧ-тан {avg+5 if avg < 95 else 100} балл алу мүмкіндігі бар."
    
    if "рейтинг" in p or "лидер" in p:
        return "Рейтингті 'Лидерборд' бөлімінен көре аласыз. Қазіргі көшбасшы: Айым К."

    return f"Сәлем {user_name}! Мен Аламанмын. Оқу үлгерімі, бағалар немесе сабақ кестесі туралы сұрасаңыз болады."

def get_leaderboard_data(bilim):
    data = []
    for s in bilim["students"]:
        grades = [g["score"] for g in s["grades_timeline"]]
        avg = sum(grades)/len(grades) if grades else 0
        data.append({"Оқушы": s["full_name"], "Орташа балл": round(avg, 1), "Қатысу (%)": s["attendance"]["present"]})
    return pd.DataFrame(data).sort_values(by="Орташа балл", ascending=False)