import json
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
import os

from app.models import ArticleNode, Favorite, TestSession, TestQuestion
from app.extensions import db
from app.services.ai_service import ask_ai_question
from app.services.test_generator_service import generate_test_from_article

api_bp = Blueprint('api', __name__)


@api_bp.route("/ask", methods=['POST'])
@login_required
def ask_question():
    data = request.json
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Вопрос не может быть пустым'}), 400
    try:
        result = ask_ai_question(question)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Не удалось получить ответ от ИИ: {str(e)}'}), 500


@api_bp.route("/favorite/toggle/<int:article_id>", methods=['POST'])
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


@api_bp.route("/favorite/check/<int:article_id>")
@login_required
def check_favorite(article_id):
    favorite = Favorite.query.filter_by(user_id=current_user.id, article_id=article_id).first()
    return jsonify({'favorited': favorite is not None})


@api_bp.route("/dashboard/stats")
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


@api_bp.route("/articles/latest")
def api_articles_latest():
    articles = ArticleNode.query.filter_by(is_published=True).order_by(ArticleNode.created_at.desc()).limit(5).all()
    result = [{
        'id': a.id, 'title': a.title, 'slug': a.slug,
        'level_name': {0: 'Курс', 1: 'Модуль', 2: 'Тема', 3: 'Статья'}.get(a.level, 'Раздел'),
        'created_at': a.created_at.strftime('%d.%m.%Y %H:%M') if a.created_at else ''
    } for a in articles]
    return jsonify(result)


@api_bp.route("/draft/save", methods=['POST'])
@login_required
def save_draft():
    slug = request.form.get('slug')
    content = request.form.get('content', '')
    if not slug: return jsonify({'error': 'Slug не указан'}), 400

    article = ArticleNode.query.filter_by(slug=slug).first()
    if not article: return jsonify({'error': 'Статья не найдена'}), 404

    article.content_draft = content
    article.is_dirty = True
    db.session.commit()
    return jsonify({'status': 'saved'})

# МОДУЛЬ ГЕНЕРАЦИИ ТЕСТОВ
@api_bp.route("/test/generate", methods=['POST'])
@login_required
def generate_test_api():
    """Генерирует тест по статье и сохраняет сессию в БД"""
    data = request.json
    article_slug = data.get('article_slug')
    num_questions = int(data.get('num_questions', 5))
    difficulty = data.get('difficulty', 'medium')

    if not article_slug:
        return jsonify({'error': 'Не указан slug статьи'}), 400

    try:
        # 1. Генерируем тест через сервис
        test_data = generate_test_from_article(
            article_slug=article_slug,
            num_questions=num_questions,
            difficulty=difficulty
        )

        # 2. Создаём сессию тестирования в БД
        session = TestSession(
            user_id=current_user.id,
            topic=test_data['topic'],
            source_article_slug=test_data['source_article_slug'],
            num_questions=test_data['num_questions'],
            difficulty=test_data['difficulty'],
            total_questions=test_data['num_questions'],
            completed=False
        )
        db.session.add(session)
        db.session.flush()  # Получаем session.id до коммита

        # 3. Сохраняем вопросы
        for q_data in test_data['questions']:
            question = TestQuestion(
                session_id=session.id,
                question_text=q_data['question_text'],
                correct_answer_index=q_data['correct_answer_index'],
                explanation=q_data['explanation'],
                order_index=q_data['order_index']
            )
            question.set_options(q_data['options'])  # Сохраняем как JSON
            db.session.add(question)

        db.session.commit()

        # 4. Возвращаем вопросы фронтенду (БЕЗ правильных ответов!)
        questions_for_frontend = [q.to_dict(include_answer=False) for q in session.questions]

        return jsonify({
            'status': 'success',
            'session_id': session.id,
            'topic': session.topic,
            'questions': questions_for_frontend
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500


@api_bp.route("/test/submit", methods=['POST'])
@login_required
def submit_test_api():
    """Принимает ответы пользователя, проверяет их и возвращает результаты"""
    data = request.json
    session_id = data.get('session_id')
    user_answers = data.get('answers', {})  # Словарь {question_id: user_answer_index}

    if not session_id:
        return jsonify({'error': 'Не указан session_id'}), 400

    session = TestSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({'error': 'Сессия не найдена'}), 404

    if session.completed:
        return jsonify({'error': 'Этот тест уже завершён'}), 400

    correct_count = 0
    results = []

    # Проверяем каждый вопрос
    for question in session.questions:
        user_answer = user_answers.get(str(question.id))

        # Если пользователь не ответил, считаем как None
        if user_answer is not None:
            is_correct = question.check_answer(int(user_answer))
            if is_correct:
                correct_count += 1
        else:
            question.check_answer(None)  # Помечаем как неотвеченный

        results.append(question.to_dict(include_answer=True))

    # Обновляем сессию
    session.correct_answers = correct_count
    session.calculate_score()
    session.completed = True
    session.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'status': 'success',
        'score': session.score,
        'correct_answers': session.correct_answers,
        'total_questions': session.total_questions,
        'results': results
    })


@api_bp.route("/test/history", methods=['GET'])
@login_required
def test_history_api():
    """Возвращает историю пройденных тестов пользователя"""
    sessions = TestSession.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).order_by(TestSession.completed_at.desc()).limit(20).all()

    return jsonify({
        'status': 'success',
        'history': [s.to_dict() for s in sessions]
    })