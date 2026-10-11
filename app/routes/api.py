from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
import re

from app.models import ArticleNode, Favorite
from app.extensions import db
from app.services.ai_service import ask_ai_question
from app.services.tree_service import build_tree

api_bp = Blueprint('api', __name__)


@api_bp.route("/api/ask", methods=['POST'])
@login_required
def ask_question():
    """Обработка вопроса пользователя к ИИ-помощнику"""
    data = request.json
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Вопрос не может быть пустым'}), 400

    try:
        result = ask_ai_question(question)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Не удалось получить ответ от ИИ: {str(e)}'}), 500


@api_bp.route("/api/favorite/toggle/<int:article_id>", methods=['POST'])
@login_required
def toggle_favorite(article_id):
    article = ArticleNode.query.filter_by(id=article_id, is_published=True).first_or_404()
    favorite = Favorite.query.filter_by(user_id=current_user.id, article_id=article_id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'removed', 'favorited': False})
    else:
        favorite = Favorite(user_id=current_user.id, article_id=article_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'added', 'favorited': True})


@api_bp.route("/api/dashboard/stats")
def api_dashboard_stats():
    base_filter = ArticleNode.query.filter_by(is_published=True)

    level_counts = {
        'courses': base_filter.filter_by(level=0).count(),
        'modules': base_filter.filter_by(level=1).count(),
        'topics': base_filter.filter_by(level=2).count(),
        'articles': base_filter.filter_by(level=3).count()
    }

    def serialize(node):
        return {
            'id': node.id, 'title': node.title, 'slug': node.slug,
            'level_name': {0: 'Курс', 1: 'Модуль', 2: 'Тема', 3: 'Статья'}.get(node.level, 'Раздел'),
            'created_at': node.created_at.strftime('%d.%m.%Y %H:%M') if node.created_at else '',
            'updated_at': node.updated_at.strftime('%d.%m.%Y %H:%M') if node.updated_at else ''
        }

    return jsonify({
        'total': base_filter.count(),
        'levels': level_counts,
        'latest_added': [serialize(a) for a in base_filter.order_by(ArticleNode.created_at.desc()).limit(5).all()],
        'latest_updated': [serialize(u) for u in base_filter.order_by(ArticleNode.updated_at.desc()).limit(5).all()]
    })