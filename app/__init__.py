from flask import Flask, render_template
from flask_login import LoginManager
from .config import config
from .models.user import User
from .models.database import db
import os

def create_app(config_name=None):
    app = Flask(__name__)

    # Configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from .routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .routes.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .routes.student import student as student_blueprint
    app.register_blueprint(student_blueprint, url_prefix='/student')

    from .routes.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')


    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app