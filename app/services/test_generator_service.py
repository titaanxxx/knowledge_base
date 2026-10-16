"""
Сервис для генерации тестовых заданий на основе контента базы знаний.
Использует локальную LLM (Ollama) и строгий JSON-парсинг.
"""
import json
import re
import ollama

from app.models import ArticleNode
# ВАЖНО: Проверь путь! Если constants.py лежит в app/, то: from app.constants import ...
# Если в app/utils/, то: from app.utils.constants import ...
from app.constants import (
    TEST_MODEL_NAME, TEST_TEMPERATURE, TEST_TOP_P,
    TEST_MAX_TOKENS, TEST_CONTEXT_SIZE, TEST_RETRY_ATTEMPTS,
    TEST_MIN_CONTENT_LENGTH, TEST_DEFAULT_QUESTIONS, TEST_DIFFICULTIES
)


def extract_json_from_response(response_text: str) -> dict:
    """
    Извлекает чистый JSON из ответа LLM.
    Убирает markdown-обёртки (```json ... ```) и лишний текст.
    """
    # Ищем блок, начинающийся с { и заканчивающийся на }
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

    if not json_match:
        raise ValueError("JSON не найден в ответе LLM")

    json_str = json_match.group()
    # Чистим от markdown-обёртки
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*', '', json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Невалидный JSON от LLM: {str(e)}")


def validate_test_data(data: dict, expected_count: int) -> list:
    """
    Проверяет, что LLM вернула корректную структуру теста.
    """
    if 'questions' not in data or not isinstance(data['questions'], list):
        raise ValueError("В ответе отсутствует или невалиден ключ 'questions'")

    questions = data['questions']
    if len(questions) == 0:
        raise ValueError("Список вопросов пуст")

    validated = []
    for i, q in enumerate(questions, 1):
        required = ['question', 'options', 'correct_answer_index', 'explanation']
        for key in required:
            if key not in q:
                raise ValueError(f"В вопросе {i} отсутствует ключ '{key}'")

        if not isinstance(q['options'], list) or len(q['options']) != 4:
            raise ValueError(f"В вопросе {i} должно быть ровно 4 варианта ответа")

        if not (0 <= q['correct_answer_index'] <= 3):
            raise ValueError(f"В вопросе {i} correct_answer_index должен быть от 0 до 3")

        validated.append({
            'question_text': str(q['question']).strip(),
            'options': [str(opt).strip() for opt in q['options']],
            'correct_answer_index': int(q['correct_answer_index']),
            'explanation': str(q['explanation']).strip(),
            'order_index': i - 1
        })

    return validated


def generate_test_from_article(
    article_slug: str,
    num_questions: int = TEST_DEFAULT_QUESTIONS,
    difficulty: str = 'medium'
) -> dict:
    """
    Основной метод: генерирует тест по конкретной статье.
    """
    if difficulty not in TEST_DIFFICULTIES:
        difficulty = 'medium'

    print(f"\n📝 Генерация теста: статья '{article_slug}', сложность: {difficulty}")

    # 1. Получаем статью
    article = ArticleNode.query.filter_by(slug=article_slug, is_published=True).first()
    if not article:
        raise ValueError(f"Статья '{article_slug}' не найдена или не опубликована")

    if not article.content or len(article.content.strip()) < TEST_MIN_CONTENT_LENGTH:
        raise ValueError(f"Статья слишком короткая (минимум {TEST_MIN_CONTENT_LENGTH} символов)")

    # 2. Формируем промпт
    difficulty_desc = {
        'easy': 'лёгкий (проверка фактов и определений)',
        'medium': 'средний (проверка понимания концепций)',
        'hard': 'сложный (применение знаний на практике)'
    }.get(difficulty, 'средний')

    system_prompt = """Ты — профессиональный преподаватель. Твоя задача — создать тест по предоставленному тексту.
    ТРЕБОВАНИЯ:
    1. Ровно указанное количество вопросов.
    2. Ровно 4 варианта ответа (A, B, C, D) на каждый вопрос.
    3. Только один правильный ответ.
    4. Краткое объяснение правильного ответа.
    5. ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON. Никакого текста до или после JSON. Никаких markdown-обёрток.
    """

    user_prompt = f"""Создай {num_questions} вопросов уровня "{difficulty_desc}" по теме: {article.title}

УЧЕБНЫЙ ТЕКСТ:
---
{article.content}
---

ФОРМАТ JSON:
{{
  "questions": [
    {{
      "question": "Текст вопроса?",
      "options": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"],
      "correct_answer_index": 0,
      "explanation": "Почему это правильный ответ."
    }}
  ]
}}
"""

    # 3. Запрос к Ollama с механизмом повторных попыток
    last_error = None
    for attempt in range(TEST_RETRY_ATTEMPTS + 1):
        try:
            print(f"🤖 Отправка запроса в AI (попытка {attempt + 1})...")
            response = ollama.generate(
                model=TEST_MODEL_NAME,
                system=system_prompt,
                prompt=user_prompt,
                options={
                    'temperature': TEST_TEMPERATURE,
                    'top_p': TEST_TOP_P,
                    'num_predict': TEST_MAX_TOKENS,
                    'num_ctx': TEST_CONTEXT_SIZE
                }
            )

            raw_text = response['response'].strip()
            print("✅ Ответ получен, парсинг JSON...")

            # 4. Парсинг и валидация
            test_data = extract_json_from_response(raw_text)
            validated_questions = validate_test_data(test_data, num_questions)

            print(f"✅ Успешно сгенерировано {len(validated_questions)} вопросов!\n")

            return {
                'topic': article.title,
                'source_article_slug': article.slug,
                'num_questions': len(validated_questions),
                'difficulty': difficulty,
                'questions': validated_questions
            }

        except Exception as e:
            last_error = e
            print(f"⚠️ Ошибка на попытке {attempt + 1}: {str(e)}")
            if attempt < TEST_RETRY_ATTEMPTS:
                print("🔄 Пробуем ещё раз...\n")
                continue

    raise ValueError(f"Не удалось сгенерировать тест после {TEST_RETRY_ATTEMPTS + 1} попыток. Последняя ошибка: {str(last_error)}")