from app.models import ArticleNode
from app.extensions import db


def build_tree():
    """Собирает иерархическое дерево всех опубликованных статей"""
    nodes = (
        ArticleNode.query.filter_by(is_published=True)
        .order_by(ArticleNode.level, ArticleNode.order_index, ArticleNode.title)
        .all()
    )

    node_map = {n.id: n for n in nodes}
    tree = []

    for node in nodes:
        if node.parent_id is None:
            tree.append(node)
        else:
            parent = node_map.get(node.parent_id)
            if parent:
                if not hasattr(parent, '_children'):
                    setattr(parent, '_children', [])
                getattr(parent, '_children').append(node)

    def recursive_sort(items):
        items.sort(key=lambda x: (x.order_index, x.title))
        for item in items:
            if hasattr(item, '_children') and getattr(item, '_children'):
                recursive_sort(getattr(item, '_children'))
        return items

    sorted_tree = recursive_sort(tree)

    def serialize(nodes):
        res = []
        for item in nodes:
            d = {
                'id': item.id,
                'title': item.title,
                'slug': item.slug,
                'level': item.level,
                'children_count': len(getattr(item, '_children', [])),
                'has_draft': getattr(item, 'is_dirty', False) and bool(getattr(item, 'content_draft', None)),
                'children': serialize(getattr(item, '_children', [])) if hasattr(item, '_children') else []
            }
            res.append(d)
        return res

    return serialize(sorted_tree)


def get_parents_for_form():
    """Собирает иерархический список для выбора родителя в форме"""
    nodes = (
        ArticleNode.query.filter_by(is_published=True)
        .order_by(ArticleNode.level, ArticleNode.order_index, ArticleNode.title)
        .all()
    )

    parents_list = []
    icons = {0: '<i class="fa-solid fa-book"></i>', 1: '<i class="fa-solid fa-folder"></i>',
             2: '<i class="fa-solid fa-folder"></i>', 3: '<i class="fa-solid fa-file"></i>'}

    for n in nodes:
        icon = icons.get(n.level, '<i class="fa-solid fa-file"></i>')
        prefix_html = ''
        if n.level > 0:
            prefix_html = '<span class="tree-indent">' + (
                        '&nbsp;&nbsp;' * (n.level - 1)) + '<i class="fa-solid fa-caret-right"></i> </span>'

        parents_list.append({
            'id': n.id, 'title': n.title, 'level': n.level,
            'prefix_html': prefix_html, 'icon': icon
        })
    return parents_list


def get_breadcrumb_path(slug: str):
    """Собирает цепочку родителей от корня до текущей статьи"""
    path = []
    node = ArticleNode.query.filter_by(slug=slug, is_published=True).first()
    if not node:
        return path

    current = node
    while current.parent_id is not None:
        parent = db.session.get(ArticleNode, current.parent_id)
        if parent and parent.is_published:
            path.insert(0, {'title': parent.title, 'slug': parent.slug, 'level': parent.level})
            current = parent
        else:
            break

    path.append({'title': node.title, 'slug': node.slug, 'level': node.level})
    return path


def get_children_tree(parent_node):
    """Рекурсивно получает детей для узла (для страницы избранного)"""
    children = ArticleNode.query.filter_by(
        parent_id=parent_node.id, is_published=True
    ).order_by(ArticleNode.order_index, ArticleNode.title).all()

    result = []
    for child in children:
        result.append({
            'article': child,
            'children': get_children_tree(child) if child.children_count > 0 else []
        })
    return result