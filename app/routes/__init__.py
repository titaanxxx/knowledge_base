"""
Регистрация всех Blueprint'ов (маршрутов) приложения.
"""
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.api import api_bp

def register_blueprints(app):
    """Функция для регистрации всех роутов в приложении"""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')