from flask import Blueprint, render_template, redirect, session, request, url_for
from app.db import db_app
from app.profile.services import get_full_user_profile

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    email = session['user']['email']
    user_data = get_full_user_profile(email)

    if not user_data:
        return render_template("fail_user.html", message="Пользователь не найден")

    return render_template('profile.html', user=user_data)


@profile_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    email = session['user']['email']
    user = db_app.fetch_one("SELECT * FROM user_profiles WHERE email = %s", (email,))

    if request.method == 'POST':
        name = request.form.get('name')
        new_password = request.form.get('new_password')
        personality_type = request.form.get('personality_type')
        goals_raw = request.form.get('goals')

        # Обновляем поля профиля
        update_fields = {
            'name': name,
            'personality_type': personality_type
        }
        if new_password:
            update_fields['password'] = new_password

        for field, value in update_fields.items():
            db_app.execute(f"UPDATE user_profiles SET {field} = %s WHERE email = %s", (value, email))

        # Обновляем цели
        db_app.execute("DELETE FROM user_goals WHERE user_email = %s", (email,))
        goals = [g.strip() for g in goals_raw.split(',') if g.strip()]
        for goal in goals:
            db_app.insert("user_goals", {"user_email": email, "goal": goal})

        session['user']['name'] = name
        user = db_app.fetch_one("SELECT * FROM user_profiles WHERE email = %s", (email,))
        return render_template('edit_profile.html', user=user, message="Профиль обновлён!")

    return render_template('edit_profile.html', user=user)
