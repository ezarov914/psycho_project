from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import db_app
from app.courses.services import add_user_points
from app.tests.logic import save_test_results_for_user

tests_bp = Blueprint('tests', __name__)


@tests_bp.route('/choose_theme')
def choose_theme():
    themes = db_app.fetch_all("SELECT * FROM test_themes ORDER BY id")
    return render_template('choose_theme.html', themes=themes)


@tests_bp.route('/start_test/<int:theme_id>')
def start_test(theme_id):
    questions = db_app.fetch_all("""
        SELECT id as q_id, ask as text 
        FROM asks
        WHERE theme_id = %s
        ORDER BY id
    """, (theme_id,))

    if not questions:
        return "Нет вопросов в выбранной теме", 404

    session['current_theme_id'] = theme_id
    session['answers'] = []

    return redirect(url_for('tests.test_step_by_theme', theme_id=theme_id, step=1))


@tests_bp.route('/test_theme/<int:theme_id>/step/<int:step>', methods=['GET', 'POST'])
def test_step_by_theme(theme_id, step):
    questions = db_app.fetch_all("""
        SELECT id as q_id, ask as text
        FROM asks
        WHERE theme_id = %s
        ORDER BY id
    """, (theme_id,))

    if step > len(questions):
        return redirect(url_for('tests.test_result'))

    question = questions[step - 1]
    answers = db_app.fetch_all("SELECT text FROM answers WHERE ask_id = %s", (question["q_id"],))
    question["options"] = [a["text"] for a in answers]

    if request.method == 'POST':
        user_answer = request.form.get('answer')
        session.setdefault('answers', []).append(user_answer)
        session.modified = True
        return redirect(url_for('tests.test_step_by_theme', theme_id=theme_id, step=step + 1))

    return render_template('test.html', question=question, step=step, theme_id=theme_id)


@tests_bp.route('/test/<int:test_id>', methods=['GET', 'POST'])
def test(test_id):
    completed = session.get("completed_tests", [])
    if str(test_id) not in completed:
        completed.append(str(test_id))
        session["completed_tests"] = completed

    questions = db_app.fetch_all("""
        SELECT text, options 
        FROM test_questions 
        WHERE test_id = %s 
        ORDER BY question_index
    """, (test_id,))

    return render_template('test.html', questions=questions)


@tests_bp.route('/test/result')
def test_result():
    answers = session.get('answers', [])
    theme_id = session.get('current_theme_id')

    if 'user' in session and theme_id:
        save_test_results_for_user(session['user']['email'], theme_id)
        add_user_points(session['user']['email'], 15, 'test')

    return render_template("test_result.html", answers=answers)


@tests_bp.route('/submit_test', methods=['POST'])
def submit_test():
    return render_template('test_result.html')
