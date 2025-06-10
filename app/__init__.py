from flask import Flask, session
from .db import db_app

# Импорт blueprint-ов из разных модулей
from .auth.routes import auth_bp
from .courses.routes import courses_bp
from .profile.routes import profile_bp
from .tests.routes import tests_bp
from .editor.routes import editor_bp
from .main.routes import main_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-very-secret-key'

    # Регистрация blueprint-ов
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(tests_bp)
    app.register_blueprint(editor_bp)

    # Глобальный context processor для user_profile
    @app.context_processor
    def inject_user_profile():
        user = session.get('user')
        if user:
            profile = db_app.fetch_one("SELECT * FROM user_profiles WHERE email = %s", (user['email'],))
            return {'user_profile': profile}
        return {'user_profile': None}

    return app
