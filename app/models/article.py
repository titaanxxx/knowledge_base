"""
Модель статьи (узла дерева знаний).
"""
from datetime import datetime
from app.extensions import db


class ArticleNode(db.Model):
    __tablename__ = 'article_nodes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)

    content = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(500))  # Путь к резервной копии .md

    level = db.Column(db.Integer, default=3)  # 0=Курс, 1=Модуль, 2=Тема, 3=Статья
    parent_id = db.Column(db.Integer, db.ForeignKey('article_nodes.id'), nullable=True)
    order_index = db.Column(db.Integer, default=0)
    children_count = db.Column(db.Integer, default=0)

    is_published = db.Column(db.Boolean, default=True)

    fts_indexed_at = db.Column(db.DateTime, nullable=True)
    file_content_hash = db.Column(db.String(64))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # AI / Векторный поиск
    embedding = db.Column(db.PickleType, nullable=True)
    image_descriptions = db.Column(db.Text, nullable=True)

    # Черновики
    content_draft = db.Column(db.Text)
    is_dirty = db.Column(db.Boolean, default=False, nullable=False)

    # Рекурсивная связь для дерева
    children = db.relationship(
        "ArticleNode",
        backref=db.backref('parent', remote_side=[id]),
        lazy='select'
    )

    # Связь с избранным
    favorited_by = db.relationship('Favorite', backref='article', lazy='dynamic')

    def __repr__(self):
        return f'<ArticleNode {self.title}>'