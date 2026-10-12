from flask import Blueprint, render_template, request, flash, redirect, url_for
import os
import re

from app.models import ArticleNode
from app.extensions import db
from app.utils.decorators import admin_required
from app.services.tree_service import build_tree, get_parents_for_form, get_breadcrumb_path
from app.utils.markdown_utils import normalize_markdown, render_article_html

admin_bp = Blueprint('admin', __name__)


@admin_bp.route("/add_article", methods=["GET", "POST"])
@admin_required
def add_article():
    parents = get_parents_for_form()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        raw_content = request.form.get("content", "")
        submit_type = request.form.get("submit_type", "publish")

        try:
            level = int(request.form.get("level", "3"))
            parent_id_str = request.form.get("parent_id", "")
            parent_id = int(parent_id_str) if parent_id_str else None
        except ValueError:
            flash("Неверный формат уровня!", "error")
            return render_template("admin/article_form.html", tree=build_tree(), parents=parents,
                                   page_title="➕ Добавить статью")

        if not title or not raw_content:
            flash("Заполните заголовок и содержимое!", "error")
            return render_template("admin/article_form.html", tree=build_tree(), parents=parents,
                                   page_title="➕ Добавить статью")

        slug = re.sub(r'[^a-z0-9а-яё\s\-]', '', title.lower())
        slug = re.sub(r'\s+', '-', slug).strip('-')[:50]

        if ArticleNode.query.filter_by(slug=slug).first():
            flash(f"Статья '{title}' уже существует!", "error")
            return render_template("admin/article_form.html", tree=build_tree(), parents=parents,
                                   page_title="➕ Добавить статью")

        filename = f"articles/{slug}.md"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{raw_content}")

        node = ArticleNode(
            title=title, slug=slug, filename=filename, level=level,
            parent_id=parent_id, content=raw_content, is_published=True
        )

        if submit_type == 'draft':
            node.content_draft = raw_content
            node.is_dirty = True
            node.is_published = False

        db.session.add(node)
        db.session.commit()

        # Обновляем children_count у родителя
        if parent_id:
            parent = db.session.get(ArticleNode, parent_id)
            if parent:
                parent.children_count = ArticleNode.query.filter_by(parent_id=parent_id, is_published=True).count()
                db.session.commit()

        flash(f"✅ Статья '{title}' добавлена!", "success")
        return redirect(url_for("main.article", slug=slug))

    return render_template("admin/article_form.html", tree=build_tree(), parents=parents,
                           page_title="➕ Добавить статья")


@admin_bp.route("/edit_article/<slug>", methods=["GET", "POST"])
@admin_required
def edit_article(slug):
    node = ArticleNode.query.filter_by(slug=slug).first_or_404()
    parents = get_parents_for_form()

    if request.method == "GET":
        edit_content = node.content_draft if (node.is_dirty and node.content_draft) else normalize_markdown(
            node.content)

        return render_template(
            "admin/article_form.html",
            tree=build_tree(),
            article=node,
            edit_mode=True,
            edit_content=edit_content,
            parents=parents,
            page_title=f"✏️ Редактирование: {node.title}"
        )

    # POST
    submit_type = request.form.get("submit_type")
    title = request.form.get("title", "").strip()
    new_content = request.form.get("content", "")

    try:
        level = int(request.form.get("level", str(node.level)))
        parent_id_str = request.form.get("parent_id", "")
        parent_id = int(parent_id_str) if parent_id_str else None
    except ValueError:
        flash("Неверный формат уровня или родителя!", "error")
        return redirect(url_for('admin.edit_article', slug=slug))

    new_slug = re.sub(r'[^a-z0-9а-яё\s\-]', '', title.lower())
    new_slug = re.sub(r'\s+', '-', new_slug).strip('-')[:50]

    existing = ArticleNode.query.filter_by(slug=new_slug).first()
    if existing and existing.id != node.id:
        flash("Статья с таким заголовком уже существует!", "error")
        return redirect(url_for('admin.edit_article', slug=slug))

    old_filename = node.filename
    new_filename = f"articles/{new_slug}.md"

    try:
        os.makedirs(os.path.dirname(new_filename), exist_ok=True)
        with open(new_filename, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{new_content}")

        if old_filename and old_filename != new_filename and os.path.exists(old_filename):
            os.remove(old_filename)

        node.title = title
        node.slug = new_slug
        node.filename = new_filename
        node.level = level
        node.parent_id = parent_id

        if submit_type == 'publish':
            node.content = new_content
            node.content_draft = None
            node.is_dirty = False
            node.is_published = True
            flash("✅ Статья успешно опубликована!", "success")
        elif submit_type == 'draft':
            node.content_draft = new_content
            node.is_dirty = True
            flash("💾 Черновик сохранен.", "info")

        db.session.commit()
        return redirect(url_for("main.article", slug=new_slug))

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Ошибка: {str(e)}", "error")
        return redirect(url_for('admin.edit_article', slug=slug))


@admin_bp.route("/delete_article/<slug>", methods=["POST"])
@admin_required
def delete_article(slug):
    node = ArticleNode.query.filter_by(slug=slug).first_or_404()
    try:
        # Обновляем children_count у родителя
        if node.parent_id:
            parent = db.session.get(ArticleNode, node.parent_id)
            if parent:
                parent.children_count = max(0, parent.children_count - 1)

        if node.filename and os.path.exists(node.filename):
            os.remove(node.filename)
        db.session.delete(node)
        db.session.commit()
        flash("Статья удалена", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка удаления: {str(e)}", "error")
    return redirect(url_for("main.knowledge"))