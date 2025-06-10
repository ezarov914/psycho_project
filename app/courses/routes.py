from flask import Blueprint, render_template, request, redirect, url_for, session
from collections import defaultdict
from app.db import db_app
from app.courses.services import (
    get_lesson_by_id,
    get_lessons_by_course,
    get_next_lesson,
    get_previous_lesson,
    add_user_points
)

courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/courses')
def courses():
    show_email_prompt = 'user' not in session and not session.get('email_collected')
    courses = db_app.fetch_all("SELECT * FROM main_courses WHERE available = TRUE ORDER BY id")
    return render_template('courses.html', courses=courses, show_email_prompt=show_email_prompt)


@courses_bp.route('/basic_courses')
def basic_courses():
    show_email_prompt = 'user' not in session and not session.get('email_collected')
    courses = db_app.fetch_all("SELECT * FROM author_courses WHERE available = TRUE ORDER BY id")
    return render_template("basic_courses.html", courses=courses, show_email_prompt=show_email_prompt)


@courses_bp.route('/submit_email', methods=['POST'])
def submit_email():
    email = request.form.get('email')
    if email:
        session['email_collected'] = True
        session['guest_email'] = email

        existing = db_app.fetch_one("SELECT * FROM guest_emails WHERE email = %s", (email,))
        if not existing:
            db_app.insert("guest_emails", {"email": email})

    return redirect(request.referrer or url_for('courses.courses'))


@courses_bp.route('/course/<course_id>')
def course(course_id):
    show_email_prompt = 'user' not in session and not session.get('email_collected')
    course = db_app.fetch_one("SELECT * FROM main_courses WHERE id = %s", (course_id,))
    if not course:
        return render_template("fail_course.html")

    lessons = db_app.fetch_all("SELECT * FROM levels_course WHERE chapter_id = %s", (course_id,))
    for lesson in lessons:
        lesson_id = db_app.fetch_all(
            "SELECT id FROM lessons WHERE course_id = %s ORDER BY id", (lesson['id'],)
        )[0]
        lesson["lesson_id"] = int(lesson_id["id"])

    steps = defaultdict(lambda: defaultdict(list))
    for lesson in lessons:
        steps[lesson["step"]][lesson["level"]].append(lesson)
    steps = dict(steps)

    return render_template("course.html",
                           course_id=course_id,
                           steps=steps,
                           show_email_prompt=show_email_prompt)


@courses_bp.route('/lesson/<lesson_id>', methods=['GET', 'POST'])
def lesson(lesson_id):
    lesson = get_lesson_by_id(lesson_id)
    if not lesson:
        return render_template('fail_course.html'), 404

    prev_lesson = get_previous_lesson(lesson)
    next_lesson = get_next_lesson(lesson)

    if lesson.get("type") == "test":
        if request.method == "POST":
            answer = request.form.get("answer")
            session.setdefault("answers", []).append(answer)
            if 'user' in session:
                add_user_points(session['user']['email'], 10, 'lesson')
            if next_lesson:
                return redirect(url_for("courses.lesson", lesson_id=next_lesson["id"]))
            return redirect(url_for("tests.test_result"))

        return render_template("test_step.html",
                               step=lesson_id,
                               question=lesson["question"],
                               character_name="Алекс")

    content_items = db_app.fetch_all(
        "SELECT * FROM content WHERE lesson_id = %s ORDER BY lesson_page", (lesson_id,)
    )
    qa_page_ids = [c['id'] for c in content_items if c['type'] == 'qa']

    questions = {}
    if qa_page_ids:
        placeholders = ','.join(['%s'] * len(qa_page_ids))
        rows = db_app.fetch_all(
            f"SELECT lesson_page, question, answer FROM questions WHERE lesson_page IN ({placeholders})",
            tuple(qa_page_ids)
        )
        questions = {q['lesson_page']: q for q in rows}

    return render_template(
        "lesson.html",
        lesson=lesson,
        lesson_pages=content_items,
        questions=questions,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson
    )
