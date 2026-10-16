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
TEST_TEMPERATURE = 0.7
TEST_TOP_P = 0.9
TEST_MAX_TOKENS = 4096      # Тесты длиннее, нужно больше токенов
TEST_CONTEXT_SIZE = 12000

# Логика генерации
TEST_RETRY_ATTEMPTS = 2             # Количество попыток при невалидном JSON
TEST_MIN_CONTENT_LENGTH = 50        # Минимальная длина статьи для теста
TEST_DEFAULT_QUESTIONS = 5          # Вопросы по умолчанию
TEST_DIFFICULTIES = ['easy', 'medium', 'hard'] # Допустимые уровни