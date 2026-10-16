"""
Глобальные константы приложения.
"""

# Уровни иерархии статей
LEVEL_COURSE = 0
LEVEL_MODULE = 1
LEVEL_TOPIC = 2
LEVEL_ARTICLE = 3

# Словарь для отображения уровней
LEVEL_NAMES = {
    LEVEL_COURSE: 'Курс',
    LEVEL_MODULE: 'Модуль',
    LEVEL_TOPIC: 'Тема',
    LEVEL_ARTICLE: 'Статья'
}

# Иконки Font Awesome для уровней
LEVEL_ICONS = {
    LEVEL_COURSE: '<i class="fa-solid fa-book"></i>',
    LEVEL_MODULE: '<i class="fa-solid fa-folder"></i>',
    LEVEL_TOPIC: '<i class="fa-solid fa-folder"></i>',
    LEVEL_ARTICLE: '<i class="fa-solid fa-file"></i>'
}

# Эмодзи для уровней (для форм)
LEVEL_EMOJIS = {
    LEVEL_COURSE: '📖',
    LEVEL_MODULE: '📁',
    LEVEL_TOPIC: '📂',
    LEVEL_ARTICLE: '📄'
}

# Настройки AI
AI_MODEL_NAME = 'qwen:7b'
AI_TEMPERATURE = 0.6
AI_TOP_P = 0.9
AI_TOP_K = 40
AI_MAX_TOKENS = 1000
AI_CONTEXT_SIZE = 8096
AI_REPEAT_PENALTY = 1.2

# Кэш векторов (в минутах)
VECTOR_CACHE_TTL_MINUTES = 5
MAX_CONTEXT_CHARS = 2000
TOP_K_RELEVANT_ARTICLES = 3

# НАСТРОЙКИ ГЕНЕРАЦИИ ТЕСТОВ
TEST_MODEL_NAME = 'qwen:7b'
TEST_TEMPERATURE = 0.5
TEST_TOP_P = 0.85

# БЮДЖЕТ КОНТЕКСТА
TEST_CONTEXT_SIZE = 8192
TEST_MAX_TOKENS = 6000
TEST_MAX_ARTICLE_CHARS = 4000

# Надёжность
TEST_RETRY_ATTEMPTS = 2
TEST_TIMEOUT_SECONDS = 180
TEST_KEEP_ALIVE = '5m'

TEST_MIN_CONTENT_LENGTH = 50
TEST_DEFAULT_QUESTIONS = 5
TEST_DIFFICULTIES = ['easy', 'medium', 'hard']

TEST_BATCH_SIZE = 5                 # Максимум вопросов за один запрос к LLM
TEST_MAX_QUESTIONS = 20             # Абсолютный максимум для пользователя
TEST_REQUIRE_EXPLANATION = True