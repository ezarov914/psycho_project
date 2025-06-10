from datetime import date, timedelta
from app.db import db_app


def get_lesson_by_id(lesson_id):
    return db_app.fetch_one("SELECT * FROM lessons WHERE id = %s", (str(lesson_id),))


def get_lessons_by_course(course_id):
    return db_app.fetch_all("SELECT * FROM lessons WHERE course_id = %s ORDER BY id", (course_id,))


def get_previous_lesson(current_lesson):
    lessons = get_lessons_by_course(current_lesson["course_id"])
    for i, lesson in enumerate(lessons):
        if lesson["id"] == current_lesson["id"] and i > 0:
            return lessons[i - 1]
    return None


def get_next_lesson(current_lesson):
    lessons = get_lessons_by_course(current_lesson["course_id"])
    for i, lesson in enumerate(lessons):
        if lesson["id"] == current_lesson["id"] and i < len(lessons) - 1:
            return lessons[i + 1]
    return None


def add_user_points(email, points, activity_type):
    today = date.today()
    user = db_app.fetch_one("SELECT * FROM user_points WHERE email = %s", (email,))

    if not user:
        db_app.insert("user_points", {
            "email": email,
            "total_points": points,
            "last_activity_date": today,
            "streak_days": 1
        })
    else:
        streak = user['streak_days']
        last_date = user['last_activity_date']
        if last_date == today - timedelta(days=1):
            streak += 1
        elif last_date != today:
            streak = 1

        db_app.execute("""
            UPDATE user_points SET 
                total_points = total_points + %s,
                last_activity_date = %s,
                streak_days = %s
            WHERE email = %s
        """, (points, today, streak, email))

    db_app.insert("user_activity_log", {
        "email": email,
        "activity_date": today,
        "points": points,
        "activity_type": activity_type
    })
