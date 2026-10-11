import os
from pathlib import Path
from flask import Flask
from app.config import config_by_name
from app.extensions import db, login_manager, migrate

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    # 1. Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
    Path(app.config['ARTICLES_BACKUP_FOLDER']).mkdir(parents=True, exist_ok=True)

    # 3. Создаем таблицы
    with app.app_context():
        db.create_all()

    return app