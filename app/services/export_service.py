"""
Сервис для экспорта статей в PDF и Markdown.
"""
import os
import re
import shutil
import tempfile
import subprocess
import urllib.parse
from flask import current_app, send_file, Response

from app.models import ArticleNode


def export_to_markdown(slug: str) -> Response:
    """Экспорт статьи в Markdown файл"""
    node = ArticleNode.query.filter_by(slug=slug, is_published=True).first_or_404()

    file_content = f"# {node.title}\n\n"
    if node.content:
        file_content += node.content

    safe_filename = re.sub(r'[^\w.\-]', '_', slug)
    if not safe_filename.endswith('.md'):
        safe_filename = f"{safe_filename}.md"

    filename_utf8 = urllib.parse.quote(safe_filename)

    response = Response(file_content, mimetype='text/plain; charset=utf-8')
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{filename_utf8}"
    response.headers["Content-Length"] = len(file_content.encode('utf-8'))

    return response


def export_to_pdf(slug: str):
    """Экспорт статьи в PDF через Pandoc + LaTeX"""
    node = ArticleNode.query.filter_by(slug=slug, is_published=True).first_or_404()

    temp_dir = tempfile.gettempdir()
    md_filename = f"{node.slug}_export.md"
    pdf_filename = f"{node.slug}.pdf"

    md_path = os.path.join(temp_dir, md_filename)
    pdf_path = os.path.join(temp_dir, pdf_filename)

    try:
        # 1. Поиск Pandoc
        pandoc_path = shutil.which("pandoc")
        if not pandoc_path:
            default_pandoc = r"C:\Program Files\Pandoc\pandoc.exe"
            if os.path.exists(default_pandoc):
                pandoc_path = default_pandoc
            else:
                return None, "❌ Pandoc не найден. Установите его: https://pandoc.org/installing.html"

        # 2. Поиск XeLaTeX
        xelatex_path = shutil.which("xelatex")
        if not xelatex_path:
            default_xelatex = r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe"
            if os.path.exists(default_xelatex):
                xelatex_path = default_xelatex
            else:
                pdflatex_path = shutil.which("pdflatex") or r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe"
                if os.path.exists(pdflatex_path):
                    xelatex_path = pdflatex_path
                else:
                    return None, "❌ LaTeX не найден. Установите MiKTeX: https://miktex.org/download"

        content = node.content

        # Обработка путей к картинкам
        app_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        static_path = os.path.join(app_root, 'app', 'static').replace('\\', '/')

        def fix_image_paths(match):
            url = match.group(1)
            if url.startswith('/static/'):
                local_path = static_path + url[7:]
                return f'![]({local_path})'
            return match.group(0)

        content = re.sub(r'!\[(.*?)\]\((/static/.*?)\)', fix_image_paths, content)

        # 3. Формирование MD-файла
        safe_title_ascii = re.sub(r'[^\w\s\-\.\,]', '', node.title)

        md_text = f"""---
title: "{safe_title_ascii}"
author: "База знаний"
lang: ru-RU
fontsize: 12pt
mainfont: "Times New Roman" 
sansfont: "Arial"
monofont: "Courier New"
geometry: margin=2cm
header-includes: |
    \\usepackage{{amsmath}}
    \\usepackage{{amssymb}}
    \\usepackage{{unicode-math}} 
---

# {node.title}

{content}
"""

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_text)

        # 4. Запуск конвертации
        cmd = [
            pandoc_path,
            md_path,
            '-o', pdf_path,
            '--pdf-engine=' + xelatex_path
        ]

        print(f"[EXPORT] Запуск: {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=False, shell=False, timeout=120
        )

        if result.returncode != 0:
            error_log = ""
            if result.stderr:
                try:
                    error_log = result.stderr.decode('utf-8', errors='ignore')
                except Exception:
                    pass
            return None, f"❌ Ошибка при создании PDF:<br><pre>{error_log[:500]}</pre>"

        if not os.path.exists(pdf_path):
            return None, "❌ PDF файл не был создан."

        print("[EXPORT] Успех!")
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"{node.title}.pdf",
            mimetype='application/pdf'
        ), None

    except Exception as e:
        print(f"[EXPORT CRITICAL EXCEPTION] {str(e)}")
        return None, f"❌ Критическая ошибка: {str(e)}"

    finally:
        # Очистка временных файлов
        base_name = os.path.splitext(md_path)[0]
        cleanup_exts = ['.md', '.tex', '.log', '.aux', '.out', '.toc', '.pdf']
        for ext in cleanup_exts:
            path = base_name + ext
            if os.path.exists(path):
                try:
                    os.remove(path)
                except (PermissionError, OSError):
                    pass