"""
Модель избранного (связь пользователь-статья).
"""
from datetime import datetime
from app.extensions import db


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article_nodes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Уникальность: пользователь не может добавить одну статью дважды
    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='unique_favorite'),
    )

    def __repr__(self):
        return f'<Favorite user={self.user_id} article={self.article_id}>'