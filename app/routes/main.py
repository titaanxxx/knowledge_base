import os
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, jsonify, current_app
from flask_login import current_user, login_required
from markupsafe import Markup
from werkzeug.utils import secure_filename

from app.models import ArticleNode, Favorite
from app.extensions import db
from app.services.tree_service import build_tree, get_breadcrumb_path, get_parents_for_form
from app.utils.markdown_utils import prepare_markdown, render_article_html, normalize_markdown
from app.utils.file_utils import allowed_file
from app.utils.decorators import admin_required
from app.services.export_service import export_to_markdown, export_to_pdf

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
@main_bp.route("/knowledge")
def knowledge():
    tree = build_tree()
    articles = (
        ArticleNode.query.filter(
            ArticleNode.children_count == 0,
            ArticleNode.is_published == True
        ).order_by(ArticleNode.created_at.desc()).limit(10).all()
    )
    return render_template("index.html", tree=tree, articles=articles, page_title="База знаний")


@main_bp.route("/courses")
def courses():
    tree = build_tree()
    courses_list = ArticleNode.query.filter_by(level=0, is_published=True).all()
    return render_template("courses.html", tree=tree, articles=courses_list, page_title="Курсы")


@main_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        flash("Введите поисковый запрос", "info")
        return redirect(url_for("main.knowledge"))

    tree = build_tree()
    results = (
        ArticleNode.query.filter(
            ArticleNode.is_published.is_(True),
            (ArticleNode.title.ilike(f"%{query}%") | ArticleNode.content.ilike(f"%{query}%"))
        ).order_by(ArticleNode.title).limit(20).all()
    )

    # Простое отображение результатов
    search_results = [{'article': r, 'fragments': []} for r in results]

    return render_template("search_results.html", tree=tree, results=search_results, query=query,
                           page_title=f"Поиск: {query}")


@main_bp.route("/article/<slug>")
def article(slug):
    tree = build_tree()
    node = ArticleNode.query.filter_by(slug=slug, is_published=True).first_or_404()

    processed_content = prepare_markdown(node.content or "")
    html_content = render_article_html(processed_content)
    breadcrumbs = get_breadcrumb_path(slug)

    # Получаем ID избранных статей текущего пользователя
    favorited_article_ids = set()
    if current_user.is_authenticated:
        favorited_article_ids = {fav.article_id for fav in Favorite.query.filter_by(user_id=current_user.id).all()}

    # Находим предыдущую и следующую статьи того же уровня
    prev_article = None
    next_article = None

    if node.parent_id:
        siblings = ArticleNode.query.filter_by(
            parent_id=node.parent_id,
            is_published=True
        ).order_by(ArticleNode.order_index, ArticleNode.title).all()
    else:
        siblings = ArticleNode.query.filter_by(
            parent_id=None,
            level=node.level,
            is_published=True
        ).order_by(ArticleNode.order_index, ArticleNode.title).all()

    for i, sibling in enumerate(siblings):
        if sibling.id == node.id:
            if i > 0:
                prev_article = siblings[i - 1]
            if i < len(siblings) - 1:
                next_article = siblings[i + 1]
            break

    return render_template(
        "article.html",
        tree=tree,
        article=node,
        content_html=Markup(html_content),
        breadcrumbs=breadcrumbs,
        page_title=node.title,
        prev=prev_article,
        next_article=next_article,
        favorited_article_ids=favorited_article_ids
    )


@main_bp.route("/favorites")
@login_required
def favorites():
    tree = build_tree()
    favorites_list = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc()).all()

    favorites_tree = []
    for favorite in favorites_list:
        article = favorite.article
        if not article or not article.is_published:
            continue
        favorites_tree.append({
            'favorite': favorite,
            'article': article,
            'type': {0: 'course', 1: 'module', 2: 'module', 3: 'article'}.get(article.level, 'article')
        })

    return render_template("admin/favorites.html", tree=tree, favorites_tree=favorites_tree, page_title="⭐ Избранное")


# ========== ЭКСПОРТ ==========

@main_bp.route("/export/<slug>")
def export_article(slug):
    """Экспорт статьи в Markdown"""
    return export_to_markdown(slug)


@main_bp.route("/export_pdf/<slug>")
def export_article_pdf(slug):
    """Экспорт статьи в PDF"""
    result, error = export_to_pdf(slug)
    if error:
        flash(error, "error")
        return redirect(url_for("main.article", slug=slug))
    return result


# ========== ЗАГРУЗКА ИЗОБРАЖЕНИЙ ==========

@main_bp.route("/upload-image", methods=["POST"])
@login_required
def upload_image():
    """Загрузка изображения для редактора EasyMDE"""
    if 'upload' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400

    file = request.files['upload']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Добавляем уникальность к имени файла
        import time
        unique_filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Возвращаем URL в формате, который ожидает EasyMDE
        image_url = url_for('static', filename=f'uploads/{unique_filename}')
        return jsonify({'default': image_url})

    return jsonify({'error': 'Недопустимый тип файла'}), 400