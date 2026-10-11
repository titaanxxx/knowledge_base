"""
Инициализация расширений Flask.
Этот файл импортируется в models и routes, чтобы избежать циклических импортов.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Создаем экземпляры расширений (пока без привязки к приложению)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Настройки для flask-login
login_manager.login_view = 'auth.login'  # Куда перенаправлять неавторизованных
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'info'