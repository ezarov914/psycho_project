from app.db import db_app

def get_full_user_profile(email):
    user = db_app.fetch_one("SELECT * FROM user_profiles WHERE email = %s", (email,))
    if not user:
        return None

    test_count = db_app.fetch_one("""
        SELECT COUNT(*) FROM user_tests_completed WHERE user_email = %s
    """, (email,))['count']

    course_progress = db_app.fetch_all("""
        SELECT course_id, progress FROM user_courses_progress WHERE user_email = %s
    """, (email,))
    course_progress_map = {
        f"Курс {row['course_id']}": row['progress'] for row in course_progress
    }

    traits = db_app.fetch_all("""
        SELECT t.name, ut.value 
        FROM user_traits ut
        JOIN traits t ON ut.trait_id = t.id
        WHERE ut.user_email = %s
    """, (email,))
    trait_map = {row['name']: row['value'] for row in traits}

    goals = db_app.fetch_all("SELECT goal FROM user_goals WHERE user_email = %s", (email,))
    goal_list = [g['goal'] for g in goals]

    points_info = db_app.fetch_one(
        "SELECT total_points, streak_days FROM user_points WHERE email = %s", (email,)
    )

    return {
        "name": user["name"],
        "personality_type": user["personality_type"],
        "tests_completed": test_count,
        "courses_progress": course_progress_map,
        "traits": trait_map,
        "goals": goal_list,
        "points": points_info["total_points"],
        "streak_days": points_info["streak_days"]
    }
