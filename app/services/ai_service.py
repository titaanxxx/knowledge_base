"""
Сервис для работы с ИИ: векторный поиск, кэширование, запросы к Ollama.
"""
import numpy as np
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from app.models import ArticleNode
from app.utils.markdown_utils import extract_formulas_from_markdown
from app.constants import (
    AI_MODEL_NAME, AI_TEMPERATURE, AI_TOP_P, AI_TOP_K,
    AI_MAX_TOKENS, AI_CONTEXT_SIZE, AI_REPEAT_PENALTY,
    VECTOR_CACHE_TTL_MINUTES, MAX_CONTEXT_CHARS, TOP_K_RELEVANT_ARTICLES
)

# Инициализируем модель ОДИН РАЗ при импорте модуля
print("🤖 Загрузка модели векторизации...")
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("✅ Модель загружена")

# Кэш векторов статей
article_cache = {
    'vectors': None,
    'articles': None,
    'last_updated': None
}


def search_relevant_articles(question: str, top_k: int = TOP_K_RELEVANT_ARTICLES):
    """Поиск релевантных статей по векторному сходству"""
    question_vector = embedding_model.encode(question).reshape(1, -1)

    # Проверяем, нужно ли обновить кэш
    need_update = (
            article_cache['vectors'] is None or
            article_cache['last_updated'] is None or
            datetime.now() - article_cache['last_updated'] > timedelta(minutes=VECTOR_CACHE_TTL_MINUTES)
    )

    if need_update:
        print("🔄 Обновление кэша векторов...")
        articles = ArticleNode.query.filter_by(is_published=True).all()

        valid_articles = [a for a in articles if a.embedding is not None]
        if valid_articles:
            article_cache['vectors'] = np.array([a.embedding for a in valid_articles])
            article_cache['articles'] = valid_articles
            article_cache['last_updated'] = datetime.now()
            print(f"✅ Кэш обновлён ({len(valid_articles)} статей)")

    article_matrix = article_cache['vectors']
    valid_articles = article_cache['articles']

    if article_matrix is None or len(article_matrix) == 0:
        return []

    similarities = cosine_similarity(question_vector, article_matrix)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]

    return [{
        'article': valid_articles[idx],
        'similarity': float(similarities[idx])
    } for idx in top_indices]


def prepare_article_context(article, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """Формируем контекст статьи для ИИ"""
    context_parts = []

    # 1. Заголовок
    context_parts.append(f"[Статья: {article.title}]")

    # 2. Контент (первые N символов)
    content_preview = article.content[:max_chars]
    if len(article.content) > max_chars:
        content_preview += "..."
    context_parts.append(content_preview)

    # 3. Формулы
    formulas = extract_formulas_from_markdown(article.content)
    if formulas:
        context_parts.append(formulas)

    # 4. Описание картинок
    if article.image_descriptions:
        context_parts.append(f"\nОписание схем и графиков:\n{article.image_descriptions}")

    return "\n\n".join(context_parts)


def ask_ai_question(question: str) -> dict:
    """
    Основной метод: принимает вопрос, возвращает ответ ИИ с источниками.
    """
    import ollama

    print(f"\n📩 Получен вопрос: {question}")

    # 1. Поиск релевантных статей
    print("🔍 Поиск релевантных статей...")
    relevant = search_relevant_articles(question)

    if not relevant:
        print("⚠️ Статьи не найдены")
        return {
            'answer': 'К сожалению, в базе знаний нет статей по этой теме.',
            'sources': []
        }

    print(f"✅ Найдено статей: {len(relevant)}")

    # 2. Формируем контекст
    context_parts = []
    sources = []

    for item in relevant:
        article = item['article']
        similarity = float(item['similarity'])

        context_parts.append(prepare_article_context(article))
        sources.append({
            'title': article.title,
            'slug': article.slug,
            'relevance': round(similarity * 100, 1)
        })

    context = "\n\n".join(context_parts)

    # 3. Системный промпт
    system_prompt = """Ты — интеллектуальный помощник по базе знаний.

ТВОЯ ЗАДАЧА:
1. Дать ПРЯМОЙ ОТВЕТ на вопрос.
2. Использовать ВСЮ информацию из источников.

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА:

**Ответ:** [прямой ответ, 1-2 предложения]

## Что это такое
[объяснение]

## Как это работает
[принцип]

## Примеры из источников
- ВЕСЬ код из источников — с пояснением
- ВСЕ формулы из источников — с объяснением
- ВСЮ сложность алгоритмов — O(n), O(log n)

## Преимущества и недостатки
[список]

## Источники
[названия]

ПРАВИЛА:
1. НАЧИНАЙ с "**Ответ:**"
2. ИСПОЛЬЗУЙ всю информацию из источников.
3. НЕ выдумывай.
"""

    user_prompt = f"""ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{question}

ИСТОЧНИКИ:
{context}

КРИТИЧЕСКИ ВАЖНО:
1. НАЧИНАЙ ответ СРАЗУ с "**Ответ:** ..."
2. Если в источниках есть КОД — приведи и объясни.
3. Если в источниках есть ФОРМУЛЫ — приведи и объясни.

ОТВЕТ:"""

    # 4. Запрос к Ollama
    print("🤖 Отправка запроса в AI...")

    try:
        response = ollama.generate(
            model=AI_MODEL_NAME,
            system=system_prompt,
            prompt=user_prompt,
            options={
                'temperature': AI_TEMPERATURE,
                'top_p': AI_TOP_P,
                'top_k': AI_TOP_K,
                'num_predict': AI_MAX_TOKENS,
                'num_ctx': AI_CONTEXT_SIZE,
                'repeat_penalty': AI_REPEAT_PENALTY
            }
        )

        answer = response['response'].strip()
        print("✅ Ответ получен!\n")

        return {
            'answer': answer,
            'sources': sources,
            'question': question
        }

    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        raise