"""
Сервис для генерации тестовых заданий на основе контента базы знаний.
Использует локальную LLM (Ollama) и строгий JSON-парсинг.
"""
import json
import re
import ollama

from app.models import ArticleNode
from app.constants import (
    TEST_MODEL_NAME, TEST_TEMPERATURE, TEST_TOP_P,
    TEST_MAX_TOKENS, TEST_CONTEXT_SIZE, TEST_RETRY_ATTEMPTS,
    TEST_MIN_CONTENT_LENGTH, TEST_DEFAULT_QUESTIONS, TEST_DIFFICULTIES,
    TEST_MAX_ARTICLE_CHARS, TEST_TIMEOUT_SECONDS, TEST_KEEP_ALIVE, TEST_MAX_QUESTIONS, TEST_BATCH_SIZE, TEST_REQUIRE_EXPLANATION
)


def extract_json_from_response(response_text: str) -> dict:
    """
    Извлекает чистый JSON из ответа LLM.
    Убирает markdown-обёртки, лишний текст и пытается "починить" невалидный JSON.
    """
    print(f"🔍 Сырой ответ от LLM (первые 500 символов):\n{response_text[:500]}...")

    # Ищем блок, начинающийся с { и заканчивающийся на }
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

    if not json_match:
        raise ValueError("JSON не найден в ответе LLM")

    json_str = json_match.group()

    # Чистим от markdown-обёртки
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*', '', json_str)
    json_str = json_str.strip()

    # Пытаемся "починить" частые ошибки JSON
    json_str = fix_common_json_errors(json_str)

    try:
        data = json.loads(json_str)
        # Нормализуем структуру (исправляем типичные отклонения модели)
        return normalize_test_structure(data)
    except json.JSONDecodeError as e:
        print(f"❌ Невалидный JSON после очистки:\n{json_str[:500]}...")
        raise ValueError(f"Невалидный JSON от LLM: {str(e)}")


def normalize_test_structure(data: dict) -> dict:
    """
    Агрессивная нормализация структуры JSON от LLM.
    Исправляет типичные ошибки модели:
    - 1-based индексация (4) → 0-based (3)
    - options как массив объектов → массив строк
    - разное количество вариантов → ровно 4
    """
    if 'questions' not in data:
        return data

    normalized_questions = []
    for q in data['questions']:
        normalized_q = {}

        # 1. question
        normalized_q['question'] = str(q.get('question', '')).strip()

        # 2. correct_answer_index — нормализуем индексацию
        raw_index = None
        for key in ['correct_answer_index', 'correct_index', 'answer', 'correct']:
            if key in q:
                raw_index = q[key]
                break

        # Если не нашли, ищем по паттерну
        if raw_index is None:
            for key in q:
                if 'correct' in key.lower() and 'index' in key.lower():
                    raw_index = q[key]
                    break

        # Нормализуем значение индекса
        if isinstance(raw_index, str):
            try:
                raw_index = int(raw_index)
            except (ValueError, TypeError):
                raw_index = 0
        elif not isinstance(raw_index, int):
            raw_index = 0

        # КЛЮЧЕВАЯ МАГИЯ: если индекс > 3, значит модель использует 1-based
        if raw_index > 3:
            raw_index = raw_index - 1  # 4 → 3, 5 → 4 (но потом обрежем)
        if raw_index < 0:
            raw_index = 0
        if raw_index > 3:
            raw_index = 3  # Обрезаем до максимума

        normalized_q['correct_answer_index'] = raw_index

        # 3. explanation
        normalized_q['explanation'] = str(q.get('explanation', 'Без объяснения')).strip()

        # 4. options: нормализуем до ровно 4 строк
        raw_options = q.get('options', [])

        if isinstance(raw_options, list) and len(raw_options) > 0:
            # Если это массив объектов, извлекаем текст
            if isinstance(raw_options[0], dict):
                extracted = []
                for opt in raw_options:
                    for key in ['text', 'option', 'value', 'label']:
                        if key in opt and isinstance(opt[key], str):
                            extracted.append(opt[key])
                            break
                    else:
                        # Берём первое строковое поле
                        for key, value in opt.items():
                            if isinstance(value, str) and key not in ['index', 'correct_answer']:
                                extracted.append(value)
                                break
                raw_options = extracted
            else:
                raw_options = [str(opt).strip() for opt in raw_options]
        else:
            raw_options = []

        # Гарантируем ровно 4 варианта
        if len(raw_options) < 4:
            # Дополняем пустыми строками
            raw_options.extend(['(нет варианта)'] * (4 - len(raw_options)))
        elif len(raw_options) > 4:
            # Обрезаем до 4
            raw_options = raw_options[:4]
            # Если правильный ответ был за пределами 4, ставим 0
            if normalized_q['correct_answer_index'] >= 4:
                normalized_q['correct_answer_index'] = 0

        normalized_q['options'] = raw_options

        normalized_questions.append(normalized_q)

    data['questions'] = normalized_questions
    return data


def fix_common_json_errors(json_str: str) -> str:
    """
    Пытается исправить частые ошибки JSON от LLM.
    """
    # Пропущенные запятые между объектами: } { → }, {
    json_str = re.sub(r'\}\s*\{', '}, {', json_str)

    # Лишние запятые в конце массивов: , ] → ]
    json_str = re.sub(r',\s*\]', ']', json_str)

    # Лишние запятые в конце объектов: , } → }
    json_str = re.sub(r',\s*\}', '}', json_str)

    return json_str


def validate_test_data(data: dict, expected_count: int) -> list:
    """
    Строгая валидация качества вопросов.
    Отбрасывает:
    - Обрезанные вопросы (не заканчиваются на знак препинания)
    - Слишком короткие вопросы/варианты
    - Вопросы без объяснений
    - Варианты с рассуждениями ("A. Неверно...", "Правильно...")
    """
    if 'questions' not in data or not isinstance(data['questions'], list):
        raise ValueError("В ответе отсутствует или невалиден ключ 'questions'")

    questions = data['questions']
    if len(questions) == 0:
        raise ValueError("Список вопросов пуст")

    validated = []
    for i, q in enumerate(questions, 1):
        try:
            # 1. Проверка текста вопроса
            question_text = str(q.get('question', '')).strip()

            # Отбрасываем слишком короткие вопросы
            if len(question_text) < TEST_MIN_QUESTION_LENGTH:
                print(f"  ⚠️ Вопрос {i}: слишком короткий ({len(question_text)} симв.), пропускаем")
                continue

            # Отбрасываем обрезанные вопросы (не заканчиваются на знак препинания)
            if not question_text.endswith(('.', '?', '!')):
                print(f"  ⚠️ Вопрос {i}: обрезанное предложение, пропускаем")
                continue

            # 2. Проверка вариантов ответов
            raw_options = q.get('options', [])
            if not isinstance(raw_options, list) or len(raw_options) < 4:
                print(f"  ⚠️ Вопрос {i}: недостаточно вариантов, пропускаем")
                continue

            # Нормализуем варианты
            options = []
            for opt in raw_options[:4]:
                opt_text = str(opt).strip()

                # Отбрасываем слишком короткие варианты
                if len(opt_text) < TEST_MIN_OPTION_LENGTH:
                    raise ValueError(f"Вариант слишком короткий: '{opt_text}'")

                # Отбрасываем варианты с рассуждениями
                if any(marker in opt_text.lower() for marker in [
                    'неверно,', 'правильно,', 'верно,', 'это описывает',
                    'это означает', 'не описывается', 'описывается в'
                ]):
                    raise ValueError(f"Вариант содержит рассуждение: '{opt_text[:50]}...'")

                options.append(opt_text)

            # 3. Проверка индекса правильного ответа
            correct_index = q.get('correct_answer_index', 0)
            if not isinstance(correct_index, int):
                try:
                    correct_index = int(correct_index)
                except (ValueError, TypeError):
                    correct_index = 0

            # Нормализация индекса
            if correct_index > 3:
                correct_index = correct_index - 1
            if correct_index < 0 or correct_index > 3:
                correct_index = 0

            # 4. Проверка объяснения
            explanation = str(q.get('explanation', '')).strip()
            if TEST_REQUIRE_EXPLANATION and (not explanation or explanation == 'Без объяснения'):
                print(f"  ⚠️ Вопрос {i}: нет объяснения, пропускаем")
                continue

            # 5. Всё хорошо — добавляем вопрос
            validated.append({
                'question_text': question_text,
                'options': options,
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


def generate_test_from_article(
        article_slug: str,
        num_questions: int = TEST_DEFAULT_QUESTIONS,
        difficulty: str = 'medium'
) -> dict:
    """
    Основной метод: генерирует тест по конкретной статье.
    Использует генерацию партиями для стабильности.
    """
    if difficulty not in TEST_DIFFICULTIES:
        difficulty = 'medium'

    # Ограничиваем максимум
    num_questions = min(num_questions, TEST_MAX_QUESTIONS)

    print(f"\n📝 Генерация теста: статья '{article_slug}', сложность: {difficulty}, вопросов: {num_questions}")

    # 1. Получаем статью
    article = ArticleNode.query.filter_by(slug=article_slug, is_published=True).first()
    if not article:
        raise ValueError(f"Статья '{article_slug}' не найдена или не опубликована")

    if not article.content or len(article.content.strip()) < TEST_MIN_CONTENT_LENGTH:
        raise ValueError(f"Статья слишком короткая (минимум {TEST_MIN_CONTENT_LENGTH} символов)")

    # Обрезаем контент
    article_content = article.content[:TEST_MAX_ARTICLE_CHARS]
    if len(article.content) > TEST_MAX_ARTICLE_CHARS:
        article_content += "\n[фрагмент статьи]"
        print(f"✂️ Статья обрезана до {TEST_MAX_ARTICLE_CHARS} символов")

    # 2. Разбиваем на партии
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

    print(f"📦 Будет {len(batches)} парти(й) по {TEST_BATCH_SIZE} вопросов максимум")

    # 3. Генерируем каждую партию
    all_questions = []

    for batch in batches:
        print(f"\n🔄 Генерация партии {batch['batch_num']}/{len(batches)} ({batch['size']} вопросов)...")

        try:
            batch_questions = _generate_batch(
                article_title=article.title,
                article_content=article_content,
                num_questions=batch['size'],
                difficulty=difficulty,
                batch_num=batch['batch_num'],
                total_batches=len(batches),
                start_index=batch['start_index']
            )
            all_questions.extend(batch_questions)
            print(f"✅ Партия {batch['batch_num']} успешна: {len(batch_questions)} вопросов")

        except Exception as e:
            print(f"❌ Ошибка в партии {batch['batch_num']}: {str(e)}")
            # Продолжаем генерировать остальные партии, не прерываем весь тест
            continue

    if len(all_questions) == 0:
        raise ValueError("Не удалось сгенерировать ни одного вопроса")

    # 4. Перенумеровываем вопросы
    for i, q in enumerate(all_questions):
        q['order_index'] = i

    print(f"\n✅ Итого сгенерировано: {len(all_questions)} из {num_questions} вопросов\n")

    return {
        'topic': article.title,
        'source_article_slug': article.slug,
        'num_questions': len(all_questions),
        'difficulty': difficulty,
        'questions': all_questions
    }


def _generate_batch(
        article_title: str,
        article_content: str,
        num_questions: int,
        difficulty: str,
        batch_num: int,
        total_batches: int,
        start_index: int
) -> list:
    """
    Генерирует одну партию вопросов.
    """
    difficulty_desc = {
        'easy': 'лёгкий (проверка фактов и определений)',
        'medium': 'средний (проверка понимания концепций)',
        'hard': 'сложный (применение знаний на практике)'
    }.get(difficulty, 'средний')

    system_prompt = """Ты — профессиональный преподаватель по программированию. Твоя задача — создать тест по предоставленному тексту.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. Создай РОВНО указанное количество вопросов.
2. Каждый вопрос должен иметь РОВНО 4 варианта ответа в виде МАССИВА СТРОК.
3. Только ОДИН вариант ответа правильный.
4. Укажи индекс правильного ответа: 0 для первого, 1 для второго, 2 для третьего, 3 для четвёртого.
5. Объяснение должно быть кратким (1-2 предложения) и ТОЧНЫМ.
6. ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON. Никакого текста до или после JSON.
7. НЕ ГАЛЛЮЦИНИРУЙ: правильные ответы должны быть корректными.

СТРОГАЯ СТРУКТУРА JSON:
{
  "questions": [
    {
      "question": "Текст вопроса?",
      "options": ["Первый вариант", "Второй вариант", "Третий вариант", "Четвёртый вариант"],
      "correct_answer_index": 0,
      "explanation": "Краткое объяснение."
    }
  ]
}
"""

    # Указываем модели, что это часть большего теста
    batch_context = ""
    if total_batches > 1:
        batch_context = f"\nВНИМАНИЕ: Это партия {batch_num} из {total_batches}. Вопросы должны быть уникальными и не повторять предыдущие партии."

    user_prompt = f"""Создай РОВНО {num_questions} вопросов уровня "{difficulty_desc}" по теме: {article_title}
{batch_context}
УЧЕБНЫЙ ТЕКСТ:
---
{article_content}
---

КРИТИЧЕСКИ ВАЖНО:
1. Сгенерируй РОВНО {num_questions} вопросов.
2. Каждый вопрос — ПОЛНОЕ предложение, заканчивается на "?" или "."
3. options — массив из РОВНО 4 КРАТКИХ СТРОК (не рассуждений!):
    - ПРАВИЛЬНО: "MySQL", "PostgreSQL", "MongoDB", "Oracle"
    - НЕПРАВИЛЬНО: "A. Неверно, это описывает структуру данных"
4. correct_answer_index — число от 0 до 3 (индексация с нуля).
5. explanation — краткое объяснение (1 предложение).
6. Правильные ответы должны быть ТОЧНЫМИ.
7. СТРОГО валидный JSON.

ПРИМЕР ПРАВИЛЬНОГО ВОПРОСА:
{{
    "question": "Какая СУБД является реляционной?",
    "options": ["MySQL", "MongoDB", "Redis", "Elasticsearch"],
    "correct_answer_index": 0,
    "explanation": "MySQL — это реляционная СУБД, основанная на таблицах."
}}

ОТВЕТ (только JSON):
"""

    # Запрос к Ollama с retry
    last_error = None

    for attempt in range(TEST_RETRY_ATTEMPTS + 1):
        try:
            print(f"  🤖 Попытка {attempt + 1}...")

            response = ollama.generate(
                model=TEST_MODEL_NAME,
                system=system_prompt,
                prompt=user_prompt,
                format='json',
                keep_alive=TEST_KEEP_ALIVE,
                options={
                    'temperature': TEST_TEMPERATURE,
                    'top_p': TEST_TOP_P,
                    'num_predict': TEST_MAX_TOKENS,
                    'num_ctx': TEST_CONTEXT_SIZE
                }
            )

            raw_text = response['response'].strip()

            # Парсинг и валидация
            test_data = extract_json_from_response(raw_text)
            validated_questions = validate_test_data(test_data, num_questions)

            return validated_questions

        except Exception as e:
            last_error = e
            print(f"  ⚠️ Ошибка: {str(e)}")
            if attempt < TEST_RETRY_ATTEMPTS:
                continue

    raise ValueError(f"Не удалось сгенерировать партию после {TEST_RETRY_ATTEMPTS + 1} попыток: {str(last_error)}")