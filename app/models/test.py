"""
Модели для модуля генерации тестовых заданий.
"""
from datetime import datetime
from app.extensions import db


class TestSession(db.Model):
    """Сессия тестирования — одна попытка прохождения теста."""
    __tablename__ = 'test_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Параметры теста
    topic = db.Column(db.String(200), nullable=False)  # Тема тестирования
    source_article_slug = db.Column(db.String(100))  # Slug статьи, если тест по конкретной статье
    num_questions = db.Column(db.Integer, default=5)
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard

    # Результаты
    score = db.Column(db.Integer, default=0)  # Процент правильных ответов (0-100)
    correct_answers = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)

    # Временные метки
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Связь с вопросами (One-to-Many)
    questions = db.relationship('TestQuestion', backref='session',
                                lazy=True, cascade='all, delete-orphan')

    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('test_sessions', lazy=True))

    def calculate_score(self):
        """Рассчитать процент правильных ответов."""
        if self.total_questions == 0:
            self.score = 0
        else:
            self.score = round((self.correct_answers / self.total_questions) * 100)
        return self.score

    def to_dict(self):
        """Сериализация для API."""
        return {
            'id': self.id,
            'topic': self.topic,
            'source_article_slug': self.source_article_slug,
            'num_questions': self.num_questions,
            'difficulty': self.difficulty,
            'score': self.score,
            'correct_answers': self.correct_answers,
            'total_questions': self.total_questions,
            'completed': self.completed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class TestQuestion(db.Model):
    """Вопрос в рамках сессии тестирования."""
    __tablename__ = 'test_questions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('test_sessions.id'), nullable=False)

    # Данные вопроса
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON-строка со списком вариантов
    correct_answer_index = db.Column(db.Integer, nullable=False)  # Индекс правильного ответа (0-3)
    explanation = db.Column(db.Text)  # Объяснение от ИИ

    # Ответ пользователя
    user_answer_index = db.Column(db.Integer)  # Что выбрал пользователь (None = не ответил)
    is_correct = db.Column(db.Boolean, default=False)

    # Порядок вопроса в тесте
    order_index = db.Column(db.Integer, default=0)

    def get_options(self):
        """Получить список вариантов ответа."""
        import json
        try:
            return json.loads(self.options)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_options(self, options_list):
        """Сохранить список вариантов ответа как JSON."""
        import json
        self.options = json.dumps(options_list, ensure_ascii=False)

    def check_answer(self, user_answer):
        """Проверить ответ пользователя."""
        self.user_answer_index = user_answer
        self.is_correct = (user_answer == self.correct_answer_index)
        return self.is_correct

    def to_dict(self, include_answer=False):
        """
        Сериализация для API.
        :param include_answer: Если False — не отдаём правильный ответ (для прохождения теста)
        """
        result = {
            'id': self.id,
            'question_text': self.question_text,
            'options': self.get_options(),
            'order_index': self.order_index,
            'user_answer_index': self.user_answer_index,
            'is_correct': self.is_correct
        }

        if include_answer:
            result['correct_answer_index'] = self.correct_answer_index
            result['explanation'] = self.explanation

        return result