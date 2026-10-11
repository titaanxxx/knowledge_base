from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from markupsafe import Markup

from app.models import ArticleNode, Favorite
from app.services.tree_service import build_tree, get_breadcrumb_path
from app.utils.markdown_utils import prepare_markdown, render_article_html

# Создаем Blueprint
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

    return render_template(
        "article.html", tree=tree, article=node, content_html=Markup(html_content),
        breadcrumbs=breadcrumbs, page_title=node.title, favorited_article_ids=favorited_article_ids
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
            'type': 'article'
        })

    return render_template("admin/favorites.html", tree=tree, favorites_tree=favorites_tree, page_title="⭐ Избранное")