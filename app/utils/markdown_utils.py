import re
import markdown
from markupsafe import Markup


def normalize_markdown(text: str) -> str:
    """Приводит Markdown к единому формату переносов строк"""
    if not text:
        return ""

    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Гарантируем пустую строку перед цитатами и списками
    text = re.sub(r'([^\n])\n(>)', r'\1\n\n\2', text)
    text = re.sub(r'(^)(>)', r'\1\n\2', text, flags=re.MULTILINE)
    text = re.sub(r'([^\n])\n([-*+]|\d+\.)', r'\1\n\n\2', text)
    text = re.sub(r'(^)([-*+]|\d+\.)', r'\1\n\2', text, flags=re.MULTILINE)
    # Убираем множественные пустые строки
    text = re.sub(r'\n{3,}', '\n\n', text)

    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    return '\n'.join(lines).strip()


def prepare_markdown(text: str) -> str:
    """Подготавливает текст для рендеринга, сохраняя блоки кода"""
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    result = []
    inside_code = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            inside_code = not inside_code
            result.append(line)
            continue
        if inside_code:
            result.append(line)
            continue
        result.append(line)

    text = "\n".join(result)
    text = re.sub(r"([^\n])\n(>|\d+\.\s|[-+*]\s)", r"\1\n\n\2", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def render_article_html(text: str) -> str:
    """Рендерит Markdown в HTML с поддержкой расширений"""
    processed = prepare_markdown(text or "")
    return markdown.markdown(
        processed,
        extensions=["fenced_code", "tables", "nl2br", "pymdownx.tilde", "sane_lists"]
    )


def extract_formulas_from_markdown(content: str) -> str:
    """Извлекает формулы из Markdown контента для ИИ"""
    inline_formulas = re.findall(r'\$(.*?)\$', content)
    block_formulas = re.findall(r'\$\$(.*?)\$\$', content, re.DOTALL)

    formulas_text = ""
    if inline_formulas:
        formulas_text += "\n\nФормулы (инлайн):\n"
        for i, formula in enumerate(inline_formulas[:10], 1):
            formulas_text += f"{i}. ${formula}$\n"

    if block_formulas:
        formulas_text += "\n\nФормулы (блочные):\n"
        for i, formula in enumerate(block_formulas[:10], 1):
            clean_formula = formula.strip().replace('\n', ' ')
            formulas_text += f"{i}. $$ {clean_formula} $$\n"

    return formulas_text