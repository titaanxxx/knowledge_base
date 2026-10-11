import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Базовая директория (папка knowledge_base)
basedir = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-2026-replace-in-prod')

    db_path = basedir / 'instance' / 'knowledge_base.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path.as_posix()}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = basedir / 'app' / 'static' / 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ARTICLES_BACKUP_FOLDER = basedir / 'articles'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}