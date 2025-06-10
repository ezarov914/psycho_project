from app.db import db_app

def save_test_results_for_user(email, theme_id):
    """
    Сохраняет результат прохождения теста пользователем в БД.
    """
    db_app.insert('users_tests', {
        "user_id": email,
        "test_id": theme_id
    }, returning=False)
