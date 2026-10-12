# Knowledge Base — Интеллектуальная база знаний с ИИ-помощником

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue?logo=sqlite)
![Ollama](https://img.shields.io/badge/Ollama-Qwen--7B-purple)
![License](https://img.shields.io/badge/License-MIT-green)

**Структурированная база знаний по программированию с векторным поиском и ИИ-ассистентом на базе локальной LLM**

[О проекте](#о-проекте) • [Возможности](#возможности) • [Технологии](#технологический-стек) • [Установка](#установка-и-запуск) • [Архитектура](#архитектура-проекта)

</div>

---

## О проекте

**Knowledge Base** — это веб-приложение для создания, хранения и поиска структурированных знаний. Проект решает проблему фрагментации информации: вместо разрозненных заметок вы получаете **единое дерево знаний** с иерархией:

```text
Курс → Модуль → Тема → Статья
```

Каждая статья может содержать код, формулы LaTeX, изображения и связанные материалы.

Главная особенность — **встроенный ИИ-помощник**, который работает на локальной LLM (**Qwen 7B** через Ollama). Он анализирует базу знаний с помощью **векторного поиска** (SentenceTransformers) и отвечает на вопросы пользователя, указывая конкретные источники.

> **Идея проекта:** объединить лучшие практики Obsidian/Notion с возможностями локального ИИ — без интернета, с сохранением приватности данных.

---

## Возможности

### Управление знаниями
- Иерархическое дерево статей (4 уровня: Курс → Модуль → Тема → Статья)
- Markdown-редактор **EasyMDE** с загрузкой изображений
- Поддержка формул **LaTeX** через MathJax (inline и display)
- Система черновиков с раздельным сохранением
- Нумерация строк в блоках кода при просмотре

### Поиск и навигация
- Полнотекстовый поиск по заголовкам и содержимому
- Хлебные крошки для навигации по иерархии
- Избранное для быстрого доступа к материалам
- Дашборд со статистикой и последними изменениями

### ИИ-помощник (локальный)
- Векторный поиск через **SentenceTransformers** (`paraphrase-multilingual-MiniLM-L12-v2`)
- Генерация ответов через локальную LLM **Qwen 7B** (Ollama)
- Ссылки на источники с процентом релевантности
- Кэширование векторов для быстрого поиска

### Экспорт
- Экспорт статей в **Markdown** (`.md`)
- Экспорт в **PDF** через Pandoc + XeLaTeX (кириллица и формулы)

### Пользователи и безопасность
- Регистрация и авторизация (Flask-Login)
- Роли: обычный пользователь / администратор
- Хэширование паролей (Werkzeug)

### Интерфейс
- Тёмная тема с продуманной палитрой
- Адаптивная вёрстка (desktop / tablet / mobile)
- Модульные CSS и JS
- Toast-уведомления с анимацией

---

## Технологический стек

| Категория | Технология | Назначение |
|-----------|-----------|------------|
| **Backend** | Python 3.12 + Flask 3.0 | Веб-фреймворк |
| **ORM** | SQLAlchemy 2.0 + Flask-SQLAlchemy | Работа с БД |
| **Миграции** | Flask-Migrate (Alembic) | Управление схемой БД |
| **База данных** | SQLite | Хранение данных |
| **Авторизация** | Flask-Login | Сессии пользователей |
| **Markdown** | Markdown + PyMdown Extensions | Рендеринг контента |
| **Формулы** | MathJax 3 (CDN) | LaTeX на фронтенде |
| **Редактор** | EasyMDE (CDN) | Markdown-редактор |
| **ИИ: эмбеддинги** | SentenceTransformers | Векторизация текста |
| **ИИ: генерация** | Ollama + Qwen 7B | Локальная LLM |
| **Экспорт PDF** | Pandoc + XeLaTeX | Конвертация MD → PDF |
| **Фронтенд** | HTML5 + CSS3 + Vanilla JS | Интерфейс |
| **Иконки** | Font Awesome 6 | UI-иконки |

---

## Скриншоты

<div align="center">

### Главная страница с дашбордом
![Главная страница](docs/screenshots/dashboard.png)

### Просмотр статьи с блоком кода
![Статья](docs/screenshots/article.png)

### ИИ-помощник отвечает на вопрос
![ИИ-помощник](docs/screenshots/ai-assistant.png)

### Редактор EasyMDE
![Редактор](docs/screenshots/editor.png)

</div>

> **Как добавить скриншоты:** создайте папку `docs/screenshots/` и поместите туда изображения с именами `dashboard.png`, `article.png`, `ai-assistant.png`, `editor.png`.

---

## Архитектура проекта

Проект построен по принципам **модульной архитектуры Flask** с разделением ответственности:

```text
knowledge_base/
│
├── app/                          # Основной пакет приложения
│   ├── __init__.py               # Фабрика приложений (create_app)
│   ├── config.py                 # Конфигурация + загрузка .env
│   ├── extensions.py             # db, login_manager, migrate
│   │
│   ├── models/                   # Модели SQLAlchemy
│   │   ├── user.py               # User (пользователи)
│   │   ├── article.py            # ArticleNode (статьи)
│   │   └── favorite.py           # Favorite (избранное)
│   │
│   ├── routes/                   # Blueprint'ы (маршруты)
│   │   ├── main.py               # Главная, статьи, поиск
│   │   ├── auth.py               # Вход, регистрация
│   │   ├── admin.py              # CRUD статей
│   │   └── api.py                # REST API (ИИ, избранное)
│   │
│   ├── services/                 # Бизнес-логика
│   │   ├── ai_service.py         # Векторный поиск + Ollama
│   │   ├── tree_service.py       # Построение дерева
│   │   └── export_service.py     # Экспорт в PDF/MD
│   │
│   ├── utils/                    # Вспомогательные функции
│   │   ├── markdown_utils.py     # Парсинг Markdown
│   │   ├── decorators.py         # @admin_required
│   │   └── file_utils.py         # Валидация файлов
│   │
│   ├── templates/                # Jinja2-шаблоны
│   │   ├── base.html             # Общий каркас
│   │   ├── index.html            # Главная
│   │   ├── article.html          # Страница статьи
│   │   ├── search_results.html   # Результаты поиска
│   │   ├── courses.html          # Список курсов
│   │   └── admin/                # Админ-шаблоны
│   │
│   └── static/                   # Статика
│       ├── css/                  # Модульные CSS
│       ├── js/                   # Модульные JS
│       └── uploads/              # Загруженные изображения
│
├── instance/                     # Приватные данные (в .gitignore)
│   └── knowledge_base.db         # База данных SQLite
│
├── articles/                     # Резервные копии .md файлов
├── .env                          # Секреты (в .gitignore)
├── run.py                        # Точка входа
└── README.md                     # Этот файл
```

### Принципы архитектуры

- **Разделение ответственности:** маршруты (`routes/`) только обрабатывают HTTP, бизнес-логика — в `services/`, работа с БД — в `models/`.
- **Blueprint'ы:** каждый модуль (`main`, `auth`, `admin`, `api`) — независимый «отдел» приложения.
- **Расширения:** `db`, `login_manager`, `migrate` инициализируются в `extensions.py` и подключаются в фабрике `create_app`.
- **Наследование шаблонов:** `base.html` — каркас, остальные страницы наследуют его через `{% extends %}`.
- **Модульный фронтенд:** CSS и JS разбиты по логическим блокам для удобства поддержки.

---

## Установка и запуск

### Предварительные требования

- Python 3.10+
- [Ollama](https://ollama.com/download) — для ИИ-помощника
- [Pandoc](https://pandoc.org/installing.html) + [MiKTeX](https://miktex.org/download) — опционально, для экспорта в PDF

### 1. Клонирование репозитория

```bash
git clone [https://github.com/titaanxx/knowledge-base.git](https://github.com/titaanxx/knowledge-base.git)
cd knowledge-base
```

### 2. Создание виртуального окружения

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта (или скопируйте из `.env.example`):

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///knowledge_base.db
```

### 5. Запуск Ollama (для ИИ-помощника)

```bash
ollama serve
ollama pull qwen:7b
```

### 6. Запуск приложения

```bash
python run.py
```

Откройте в браузере: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Использование

### Добавление статей
1. Войдите как администратор
2. Нажмите **«Добавить статью»** в сайдбаре
3. Выберите уровень (Курс / Модуль / Тема / Статья)
4. Напишите содержимое в Markdown
5. Нажмите **«Опубликовать»**

### Задать вопрос ИИ
1. Нажмите кнопку **«Задать вопрос ИИ»** в шапке
2. Введите вопрос (например: *«Что такое формула Гаусса?»*)
3. ИИ проанализирует базу знаний и ответит со ссылками на источники

### Экспорт статьи
- Нажмите иконку **PDF** для экспорта в PDF
- Нажмите иконку **Markdown** для скачивания `.md` файла

---

## Roadmap

- [ ] Полнотекстовый поиск через FTS5 (SQLite)
- [ ] Теги и категории для статей
- [ ] Комментарии к статьям
- [ ] История изменений (версионирование)
- [ ] Экспорт всего курса в один PDF
- [ ] PWA для офлайн-доступа
- [ ] Интеграция с GitHub для синхронизации

---

## Лицензия

MIT License — свободное использование с указанием авторства.

---

## Автор

**Владислав Андреевич** — Fullstack Python Developer

- Email: [mazdawy2019@gmail.com](mailto:mazdawy2019@gmail.com)
- GitVerse: [gitverse.ru/titanxxx](https://gitverse.ru/titanxxx)
- GitHub: [github.com/titaanxxx](https://github.com/titaanxxx)

<div align="center">

Если проект был полезен — поставьте звезду на GitHub.

*Сделано с любовью и большим количеством кофе.*

</div>