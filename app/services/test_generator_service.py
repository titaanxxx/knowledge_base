"""
Сервис для генерации тестовых заданий на основе контента базы знаний.
Использует локальную LLM (Ollama), JSON-формат, нормализацию и валидацию качества.
"""

import json
import re
import ollama

from app.models import ArticleNode
from app.constants import (
    TEST_MODEL_NAME,
    TEST_TEMPERATURE,
    TEST_TOP_P,
    TEST_REPEAT_PENALTY,
    TEST_MAX_TOKENS,
    TEST_CONTEXT_SIZE,
    TEST_RETRY_ATTEMPTS,
    TEST_MIN_CONTENT_LENGTH,
    TEST_DEFAULT_QUESTIONS,
    TEST_DIFFICULTIES,
    TEST_MAX_ARTICLE_CHARS,
    TEST_TIMEOUT_SECONDS,
    TEST_KEEP_ALIVE,
    TEST_MAX_QUESTIONS,
    TEST_BATCH_SIZE,
    TEST_REQUIRE_EXPLANATION,
    TEST_MIN_QUESTION_LENGTH,
    TEST_MIN_OPTION_LENGTH,
)


# Клиент Ollama
llm_client = ollama.Client(
    host='http://localhost:11434',
    timeout=TEST_TIMEOUT_SECONDS
)


# ==========================================
# ИЗВЛЕЧЕНИЕ И ОЧИСТКА JSON
# ==========================================

def extract_json_from_response(response_text: str) -> dict:
    """
    Извлекает JSON из ответа LLM и нормализует структуру.
    """
    print(f"🔍 Сырой ответ от LLM (первые 700 символов):\n{response_text[:700]}...")

    text = response_text.strip()

    # Убираем markdown-обёртки
    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()

    # Сначала пробуем распарсить весь ответ как JSON
    try:
        data = json.loads(text)
        return normalize_test_structure(data)
    except json.JSONDecodeError:
        pass

    # Если не получилось — ищем JSON-объект внутри текста
    json_match = re.search(r'\{.*\}', text, re.DOTALL)

    if not json_match:
        raise ValueError("JSON не найден в ответе LLM")

    json_str = json_match.group()
    json_str = fix_common_json_errors(json_str)

    try:
        data = json.loads(json_str)
        return normalize_test_structure(data)
    except json.JSONDecodeError as e:
        print(f"❌ Невалидный JSON после очистки:\n{json_str[:700]}...")
        raise ValueError(f"Невалидный JSON от LLM: {str(e)}")


def fix_common_json_errors(json_str: str) -> str:
    """Исправляет частые ошибки JSON."""
    json_str = re.sub(r'\}\s*\{', '}, {', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    json_str = re.sub(r',\s*\}', '}', json_str)
    return json_str.strip()


# ==========================================
# НОРМАЛИЗАЦИЯ СТРУКТУРЫ
# ==========================================

def normalize_test_structure(data: dict) -> dict:
    """
    Приводит разные варианты ответа модели к единому формату.
    Поддерживает разные названия полей: question/title, options/answers/variants и т.д.
    """

    if not isinstance(data, dict):
        raise ValueError("Ответ LLM не является JSON-объектом")

    # Если модель вернула не questions, а сразу список
    if 'questions' not in data and isinstance(data.get('test'), list):
        data['questions'] = data['test']

    if 'questions' not in data:
        return data

    if not isinstance(data['questions'], list):
        raise ValueError("Поле 'questions' должно быть списком")

    normalized_questions = []

    for q in data['questions']:
        if not isinstance(q, dict):
            continue

        normalized_q = {}

        # Текст вопроса (поддерживаем разные названия полей)
        question_text = (
            q.get('question')
            or q.get('question_text')
            or q.get('title')
            or q.get('text')
            or ''
        )
        normalized_q['question'] = str(question_text).strip()

        # Варианты ответа
        raw_options = q.get('options') or q.get('answers') or q.get('variants') or []
        options = normalize_options(raw_options)
        normalized_q['options'] = options

        # Индекс правильного ответа
        raw_index = None
        for key in [
            'correct_answer_index',
            'correct_index',
            'answer_index',
            'correctAnswerIndex',
            'correct',
            'answer'
        ]:
            if key in q:
                raw_index = q[key]
                break

        normalized_q['correct_answer_index'] = normalize_correct_index(raw_index, options)

        # Объяснение (поддерживаем разные названия)
        explanation = (
            q.get('explanation')
            or q.get('reason')
            or q.get('comment')
            or q.get('description')
            or ''
        )
        normalized_q['explanation'] = str(explanation).strip()

        normalized_questions.append(normalized_q)

    data['questions'] = normalized_questions
    return data


def normalize_options(raw_options) -> list:
    """Нормализует варианты ответов."""
    options = []

    if isinstance(raw_options, dict):
        for key in sorted(raw_options.keys()):
            options.append(str(raw_options[key]).strip())
        return options

    if not isinstance(raw_options, list):
        return []

    for opt in raw_options:
        if isinstance(opt, dict):
            value = (
                opt.get('text')
                or opt.get('option')
                or opt.get('value')
                or opt.get('label')
                or opt.get('answer')
            )

            if value is None:
                for key, val in opt.items():
                    if isinstance(val, str) and key.lower() not in [
                        'index', 'correct', 'correct_answer', 'is_correct'
                    ]:
                        value = val
                        break

            if value is not None:
                options.append(str(value).strip())
        else:
            options.append(str(opt).strip())

    # Убираем пустые варианты
    options = [opt for opt in options if opt]

    return options


def normalize_correct_index(raw_index, options: list):
    """Нормализует индекс правильного ответа."""
    if raw_index is None:
        return None

    # Если модель вернула букву A/B/C/D
    if isinstance(raw_index, str):
        value = raw_index.strip()

        letter_map = {
            'A': 0, 'B': 1, 'C': 2, 'D': 3,
            'А': 0, 'В': 1, 'С': 2, 'D': 3,
        }

        if value.upper() in letter_map:
            return letter_map[value.upper()]

        # Если модель вернула текст правильного ответа
        for idx, opt in enumerate(options):
            if value.lower() == opt.lower():
                return idx

        try:
            raw_index = int(value)
        except (ValueError, TypeError):
            return None

    if not isinstance(raw_index, int):
        return None

    # Нормальная индексация: 0-3
    if 0 <= raw_index <= 3:
        return raw_index

    # Частая ошибка модели: 1-4 вместо 0-3
    if raw_index == 4:
        return 3

    return None


# ==========================================
# ВАЛИДАЦИЯ КАЧЕСТВА
# ==========================================

def validate_test_data(data: dict, expected_count: int) -> list:
    """
    Валидирует качество вопросов.
    Отбрасывает мусор, но не слишком строгая — даём модели шанс.
    """

    if 'questions' not in data or not isinstance(data['questions'], list):
        raise ValueError("В ответе отсутствует или невалиден ключ 'questions'")

    questions = data['questions']

    if len(questions) == 0:
        raise ValueError("Список вопросов пуст")

    validated = []
    seen_questions = set()

    for i, q in enumerate(questions, 1):
        try:
            question_text = str(q.get('question', '')).strip()
            options = q.get('options', [])
            correct_index = q.get('correct_answer_index')
            explanation = str(q.get('explanation', '')).strip()

            # 1. Проверка текста вопроса
            if len(question_text) < TEST_MIN_QUESTION_LENGTH:
                print(f"  ⚠️ Вопрос {i}: слишком короткий ({len(question_text)} симв.), пропускаем")
                continue

            if not question_text.endswith(('.', '?', '!')):
                print(f"  ⚠️ Вопрос {i}: обрезанное предложение, пропускаем")
                continue

            # Проверка на явный мусор
            if contains_obvious_noise(question_text):
                print(f"  ⚠️ Вопрос {i}: содержит мусор, пропускаем")
                continue

            # Проверка на дубликаты
            normalized_question_key = question_text.lower().strip()
            if normalized_question_key in seen_questions:
                print(f"  ⚠️ Вопрос {i}: дубликат, пропускаем")
                continue

            # 2. Проверка вариантов
            if not isinstance(options, list) or len(options) != 4:
                print(f"  ⚠️ Вопрос {i}: нет ровно 4 вариантов, пропускаем")
                continue

            clean_options = []
            for opt in options:
                opt_text = str(opt).strip()

                if len(opt_text) < TEST_MIN_OPTION_LENGTH:
                    raise ValueError(f"слишком короткий вариант: {opt_text}")

                clean_options.append(opt_text)

            # Варианты должны быть уникальными
            if len(set([opt.lower() for opt in clean_options])) < 3:
                print(f"  ⚠️ Вопрос {i}: варианты повторяются, пропускаем")
                continue

            # 3. Проверка правильного ответа
            if not isinstance(correct_index, int) or not (0 <= correct_index <= 3):
                print(f"  ⚠️ Вопрос {i}: невалидный индекс правильного ответа, пропускаем")
                continue

            # 4. Проверка объяснения
            if TEST_REQUIRE_EXPLANATION:
                if not explanation or explanation.lower() in [
                    'без объяснения', 'нет объяснения', 'none', 'null'
                ]:
                    print(f"  ⚠️ Вопрос {i}: нет объяснения, пропускаем")
                    continue

                if contains_obvious_noise(explanation):
                    print(f"  ⚠️ Вопрос {i}: мусорное объяснение, пропускаем")
                    continue

            # 5. Вопрос прошёл проверку
            seen_questions.add(normalized_question_key)

            validated.append({
                'question_text': question_text,
                'options': clean_options,
                'correct_answer_index': correct_index,
                'explanation': explanation,
                'order_index': len(validated)
            })

        except Exception as e:
            print(f"  ⚠️ Вопрос {i}: {str(e)}, пропускаем")
            continue

    if len(validated) == 0:
        raise ValueError("Не удалось валидировать ни одного качественного вопроса")

    return validated


def contains_obvious_noise(text: str) -> bool:
    """
    Ловит явный мусор:
    - китайские/японские символы;
    - вопросы про "максимальную скорость на дороге", "Замечательный суп" и т.п. (галлюцинации);
    - бессмысленные шаблоны.
    """
    lower = text.lower()

    # Китайские иероглифы
    if re.search(r'[\u4e00-\u9fff]', text):
        return True

    # Японские символы
    if re.search(r'[\u3040-\u30ff]', text):
        return True

    # Очевидные галлюцинации — не относятся к теме IT/программирования
    hallucination_markers = [
        'максимальная скорость на дороге',
        'замечательный суп',
        'категория товара',
        'статистика по продажам',
        'в каком квартале',
        'алкооль',
        'спирт',
        'последственное задание',
    ]

    return any(marker in lower for marker in hallucination_markers)


# ==========================================
# ОСНОВНАЯ ГЕНЕРАЦИЯ ТЕСТА
# ==========================================

def generate_test_from_article(
        article_slug: str,
        num_questions: int = TEST_DEFAULT_QUESTIONS,
        difficulty: str = 'medium'
) -> dict:
    """Генерирует тест по конкретной статье."""

    if difficulty not in TEST_DIFFICULTIES:
        difficulty = 'medium'

    num_questions = min(num_questions, TEST_MAX_QUESTIONS)

    print(
        f"\n📝 Генерация теста: статья '{article_slug}', "
        f"сложность: {difficulty}, вопросов: {num_questions}"
    )

    article = ArticleNode.query.filter_by(
        slug=article_slug,
        is_published=True
    ).first()

    if not article:
        raise ValueError(f"Статья '{article_slug}' не найдена или не опубликована")

    if not article.content or len(article.content.strip()) < TEST_MIN_CONTENT_LENGTH:
        raise ValueError(
            f"Статья слишком короткая (минимум {TEST_MIN_CONTENT_LENGTH} символов)"
        )

    article_content = article.content[:TEST_MAX_ARTICLE_CHARS]

    if len(article.content) > TEST_MAX_ARTICLE_CHARS:
        article_content += "\n[фрагмент статьи]"
        print(f"✂️ Статья обрезана до {TEST_MAX_ARTICLE_CHARS} символов")

    # Разбиение на партии
    batches = []
    remaining = num_questions
    batch_num = 1

    while remaining > 0:
        current_batch_size = min(remaining, TEST_BATCH_SIZE)

        batches.append({
            'batch_num': batch_num,
            'size': current_batch_size,
            'start_index': num_questions - remaining
        })

        remaining -= current_batch_size
        batch_num += 1

    print(f"📦 Будет {len(batches)} парти(й), максимум по {TEST_BATCH_SIZE} вопросов")

    all_questions = []

    for batch in batches:
        print(
            f"\n🔄 Генерация партии "
            f"{batch['batch_num']}/{len(batches)} "
            f"({batch['size']} вопросов)..."
        )

        try:
            batch_questions = _generate_batch(
                article_title=article.title,
                article_content=article_content,
                num_questions=batch['size'],
                difficulty=difficulty,
                batch_num=batch['batch_num'],
                total_batches=len(batches),
                start_index=batch['start_index'],
                existing_questions=all_questions
            )

            all_questions.extend(batch_questions)

            print(
                f"✅ Партия {batch['batch_num']} успешна: "
                f"{len(batch_questions)} вопросов"
            )

        except Exception as e:
            print(f"❌ Ошибка в партии {batch['batch_num']}: {str(e)}")
            continue

    if len(all_questions) == 0:
        raise ValueError("Не удалось сгенерировать ни одного вопроса")

    # Финальная дедупликация и перенумерация
    unique_questions = []
    seen = set()

    for q in all_questions:
        key = q['question_text'].lower().strip()

        if key in seen:
            continue

        seen.add(key)
        q['order_index'] = len(unique_questions)
        unique_questions.append(q)

    print(
        f"\n✅ Итого сгенерировано: "
        f"{len(unique_questions)} из {num_questions} вопросов\n"
    )

    return {
        'topic': article.title,
        'source_article_slug': article.slug,
        'num_questions': len(unique_questions),
        'difficulty': difficulty,
        'questions': unique_questions
    }


# ==========================================
# ГЕНЕРАЦИЯ ОДНОЙ ПАРТИИ
# ==========================================

def _generate_batch(
        article_title: str,
        article_content: str,
        num_questions: int,
        difficulty: str,
        batch_num: int,
        total_batches: int,
        start_index: int,
        existing_questions: list = None
) -> list:
    """Генерирует одну партию вопросов."""

    if existing_questions is None:
        existing_questions = []

    difficulty_desc = {
        'easy': 'лёгкий: факты, определения, термины из текста',
        'medium': 'средний: понимание связей и принципов из текста',
        'hard': 'сложный: применение и анализ материала из текста'
    }.get(difficulty, 'средний')

    # Указываем модели уже созданные вопросы, чтобы не повторялась
    existing_questions_text = ""

    if existing_questions:
        existing_titles = [q['question_text'] for q in existing_questions[-10:]]
        existing_questions_text = (
            "\nУЖЕ СОЗДАННЫЕ ВОПРОСЫ (не повторяй их):\n"
            + "\n".join(f"- {title}" for title in existing_titles)
        )

    # ПРОСТОЙ И ЯСНЫЙ ПРОМПТ — без избыточных запретов
    system_prompt = f"""Ты — преподаватель по программированию. Создай тест на русском языке по предоставленному тексту.

ТЕКУЩАЯ ТЕМА: {article_title}

ФОРМАТ ОТВЕТА — СТРОГО JSON:
{{
  "questions": [
    {{
      "question": "Текст вопроса на русском языке?",
      "options": ["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"],
      "correct_answer_index": 0,
      "explanation": "Краткое объяснение на русском языке."
    }}
  ]
}}

ПРАВИЛА:
1. Все вопросы и ответы — на русском языке.
2. Вопросы должны проверять знания ТОЛЬКО из предоставленного текста.
3. Ровно 4 варианта ответа, только один правильный.
4. correct_answer_index: 0 (первый), 1 (второй), 2 (третий), 3 (четвёртый).
5. Объяснение — 1 предложение.
6. Верни ТОЛЬКО JSON, без дополнительного текста.
"""

    batch_context = ""
    if total_batches > 1:
        batch_context = (
            f"\nЭто часть {batch_num} из {total_batches}. "
            f"Создай новые уникальные вопросы."
        )

    user_prompt = f"""Создай ровно {num_questions} вопросов уровня "{difficulty_desc}" по теме: {article_title}
{batch_context}
{existing_questions_text}

ТЕКСТ СТАТЬИ:
---
{article_content}
---

ПРИМЕР ПРАВИЛЬНОГО ВОПРОСА:
{{
  "question": "Что такое реляционная база данных?",
  "options": ["База данных в виде таблиц", "База данных в виде графов", "База данных в виде документов", "База данных в виде ключ-значение"],
  "correct_answer_index": 0,
  "explanation": "Реляционная база данных хранит данные в таблицах со связями между ними."
}}

ОТВЕТЬ JSON-ОБЪЕКТОМ С КЛЮЧОМ "questions":
"""

    print(f"📌 ПРОВЕРКА: статья: '{article_title}'")
    print(f"📌 ПРОВЕРКА: начало текста: {article_content[:180]}...")

    last_error = None

    for attempt in range(TEST_RETRY_ATTEMPTS + 1):
        try:
            print(f"  🤖 Попытка {attempt + 1}...")

            response = llm_client.generate(
                model=TEST_MODEL_NAME,
                system=system_prompt,
                prompt=user_prompt,
                format='json',
                keep_alive=TEST_KEEP_ALIVE,
                options={
                    'temperature': TEST_TEMPERATURE,
                    'top_p': TEST_TOP_P,
                    'repeat_penalty': TEST_REPEAT_PENALTY,
                    'num_predict': TEST_MAX_TOKENS,
                    'num_ctx': TEST_CONTEXT_SIZE
                }
            )

            raw_text = response['response'].strip()

            if '"answer"' in raw_text and '"questions"' not in raw_text:
                raise ValueError(
                    "Модель вернула формат {{'answer': ...}} вместо {{'questions': [...]}}"
                )

            if len(raw_text) < 100:
                raise ValueError(f"Ответ слишком короткий ({len(raw_text)} символов)")

            print(f"✅ Ответ получен ({len(raw_text)} символов)")

            test_data = extract_json_from_response(raw_text)
            validated_questions = validate_test_data(test_data, num_questions)

            return validated_questions

        except Exception as e:
            last_error = e
            print(f"  ⚠️ Ошибка: {str(e)}")

            if attempt < TEST_RETRY_ATTEMPTS:
                user_prompt += """

ПРЕДЫДУЩИЙ ОТВЕТ БЫЛ НЕКАЧЕСТВЕННЫМ.
Исправь ошибки:
- только русский язык;
- только вопросы по содержанию статьи;
- только JSON с ключом "questions";
- ровно 4 варианта ответа;
- correct_answer_index от 0 до 3.
"""
                continue

    raise ValueError(
        f"Не удалось сгенерировать партию после "
        f"{TEST_RETRY_ATTEMPTS + 1} попыток: {str(last_error)}"
    )