// ===========================================
// Test Quiz: Модуль генерации и прохождения тестов
// ===========================================

// Глобальные переменные для текущей сессии теста
let currentTestSession = {
    id: null,
    articleId: null,
    articleSlug: null,
    topic: '',
    questions: [],
    currentQuestionIndex: 0,
    userAnswers: {}
};

// ========== МОДАЛКА НАСТРОЕК ==========

window.openTestSettingsModal = function(articleId, articleSlug, topic) {
    currentTestSession.articleId = articleId;
    currentTestSession.articleSlug = articleSlug;
    currentTestSession.topic = topic;

    document.getElementById('test-topic-name').textContent = topic;
    document.getElementById('test-settings-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
};

window.closeTestSettingsModal = function() {
    document.getElementById('test-settings-modal').style.display = 'none';
    document.body.style.overflow = '';
};

// Закрытие по клику вне модалки
document.addEventListener('click', (e) => {
    const modal = document.getElementById('test-settings-modal');
    if (e.target === modal) closeTestSettingsModal();
});

// ========== ГЕНЕРАЦИЯ ТЕСТА ==========

window.startTestGeneration = async function() {
    const numQuestions = document.getElementById('test-num-questions').value;
    const difficulty = document.getElementById('test-difficulty').value;

    // Закрываем модалку настроек
    closeTestSettingsModal();

    // Показываем лоадер
    showTestLoader('Модуль анализирует материал и составляет вопросы...');

    try {
        const response = await fetch('/api/test/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                article_slug: currentTestSession.articleSlug,
                num_questions: parseInt(numQuestions),
                difficulty: difficulty
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Не удалось сгенерировать тест');
        }

        // Сохраняем данные сессии
        currentTestSession.id = data.session_id;
        currentTestSession.topic = data.topic;
        currentTestSession.questions = data.questions;
        currentTestSession.currentQuestionIndex = 0;
        currentTestSession.userAnswers = {};

        hideTestLoader();

        // Переходим к прохождению теста
        renderTestQuestion();

    } catch (error) {
        hideTestLoader();
        alert('Ошибка: ' + error.message);
        console.error('Ошибка генерации теста:', error);
    }
};

// ========== ЛОАДЕР ==========

function showTestLoader(message) {
    const loader = document.createElement('div');
    loader.id = 'test-loader-overlay';
    loader.style.cssText = `
        position: fixed; inset: 0; background: rgba(6, 10, 20, 0.85);
        display: flex; align-items: center; justify-content: center;
        z-index: 99999; backdrop-filter: blur(8px);
    `;
    loader.innerHTML = `
        <div style="text-align: center; color: #e5e7eb;">
            <div class="spinner" style="margin: 0 auto 24px;"></div>
            <p style="font-size: 18px; font-weight: 600;">${message}</p>
            <p style="color: #94a3b8; margin-top: 8px;">Это может занять до 1 минуты</p>
        </div>
    `;
    document.body.appendChild(loader);
    document.body.style.overflow = 'hidden';
}

function hideTestLoader() {
    const loader = document.getElementById('test-loader-overlay');
    if (loader) {
        document.body.removeChild(loader);
        document.body.style.overflow = '';
    }
}

// ========== ПРОХОЖДЕНИЕ ТЕСТА ==========

function renderTestQuestion() {
    const question = currentTestSession.questions[currentTestSession.currentQuestionIndex];
    const total = currentTestSession.questions.length;
    const current = currentTestSession.currentQuestionIndex + 1;
    const selectedAnswer = currentTestSession.userAnswers[question.id];

    // Создаём контейнер, если его нет
    let container = document.getElementById('test-quiz-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'test-quiz-container';
        container.style.cssText = `
            position: fixed; inset: 0; background: #0b1120;
            z-index: 99998; overflow-y: auto; padding: 40px 20px;
        `;
        document.body.appendChild(container);
    }

    // Прогресс-бар
    const progressPercent = (current / total) * 100;

    container.innerHTML = `
        <div style="max-width: 800px; margin: 0 auto;">
            <!-- Шапка теста -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <div>
                    <h2 style="color: #f8fafc; margin: 0 0 4px 0;">${currentTestSession.topic}</h2>
                    <p style="color: #94a3b8; margin: 0; font-size: 14px;">Вопрос ${current} из ${total}</p>
                </div>
                <button onclick="exitTest()" style="
                    background: transparent; border: 1px solid #475569; color: #cbd5e1;
                    padding: 8px 16px; border-radius: 8px; cursor: pointer;
                ">
                    ✕ Выйти
                </button>
            </div>
            
            <!-- Прогресс-бар -->
            <div style="background: #1e293b; height: 8px; border-radius: 4px; margin-bottom: 32px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #4f8cff, #4ecdc4); height: 100%; width: ${progressPercent}%; transition: width 0.3s ease;"></div>
            </div>
            
            <!-- Вопрос -->
            <div style="background: #121826; border: 1px solid #24324a; border-radius: 16px; padding: 32px; margin-bottom: 24px;">
                <h3 style="color: #f8fafc; margin: 0 0 24px 0; font-size: 20px; line-height: 1.5;">
                    ${question.question_text}
                </h3>
                
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    ${question.options.map((option, idx) => {
                        const isSelected = selectedAnswer === idx;
                        const letter = String.fromCharCode(65 + idx);
                        return `
                            <button onclick="selectAnswer(${question.id}, ${idx})" style="
                                display: flex; align-items: center; gap: 16px;
                                background: ${isSelected ? 'rgba(79, 140, 255, 0.15)' : '#0f172a'};
                                border: 2px solid ${isSelected ? '#4f8cff' : '#24324a'};
                                color: ${isSelected ? '#f8fafc' : '#cbd5e1'};
                                padding: 16px 20px; border-radius: 12px; cursor: pointer;
                                text-align: left; font-size: 16px; transition: all 0.2s ease;
                            ">
                                <span style="
                                    display: inline-flex; align-items: center; justify-content: center;
                                    width: 32px; height: 32px; border-radius: 50%;
                                    background: ${isSelected ? '#4f8cff' : '#1e293b'};
                                    color: ${isSelected ? '#fff' : '#94a3b8'};
                                    font-weight: 700; flex-shrink: 0;
                                ">${letter}</span>
                                <span style="flex: 1;">${option}</span>
                            </button>
                        `;
                    }).join('')}
                </div>
            </div>
            
            <!-- Навигация -->
            <div style="display: flex; justify-content: space-between; gap: 12px;">
                <button onclick="previousQuestion()" ${current === 1 ? 'disabled' : ''} style="
                    background: #232d43; color: #e6eefc; border: none;
                    padding: 14px 28px; border-radius: 12px; cursor: pointer;
                    font-weight: 600; font-size: 15px;
                    ${current === 1 ? 'opacity: 0.4; cursor: not-allowed;' : ''}
                ">
                    ← Назад
                </button>
                
                ${current === total ? `
                    <button onclick="finishTest()" style="
                        background: linear-gradient(135deg, #4f8cff, #4ecdc4);
                        color: #fff; border: none; padding: 14px 32px;
                        border-radius: 12px; cursor: pointer; font-weight: 700; font-size: 15px;
                    ">
                        Завершить тест ✓
                    </button>
                ` : `
                    <button onclick="nextQuestion()" style="
                        background: linear-gradient(135deg, #4f8cff, #4ecdc4);
                        color: #fff; border: none; padding: 14px 32px;
                        border-radius: 12px; cursor: pointer; font-weight: 700; font-size: 15px;
                    ">
                        Далее →
                    </button>
                `}
            </div>
        </div>
    `;
}

window.selectAnswer = function(questionId, answerIndex) {
    currentTestSession.userAnswers[questionId] = answerIndex;
    renderTestQuestion(); // Перерисовываем для обновления UI
};

window.nextQuestion = function() {
    if (currentTestSession.currentQuestionIndex < currentTestSession.questions.length - 1) {
        currentTestSession.currentQuestionIndex++;
        renderTestQuestion();
    }
};

window.previousQuestion = function() {
    if (currentTestSession.currentQuestionIndex > 0) {
        currentTestSession.currentQuestionIndex--;
        renderTestQuestion();
    }
};

window.exitTest = function() {
    if (confirm('Вы уверены, что хотите выйти? Прогресс будет потерян.')) {
        const container = document.getElementById('test-quiz-container');
        if (container) document.body.removeChild(container);
        document.body.style.overflow = '';
    }
};

// ========== ЗАВЕРШЕНИЕ ТЕСТА ==========

window.finishTest = async function() {
    // Проверяем, что на все вопросы даны ответы
    const unanswered = currentTestSession.questions.filter(
        q => currentTestSession.userAnswers[q.id] === undefined
    );

    if (unanswered.length > 0) {
        if (!confirm(`Вы не ответили на ${unanswered.length} вопрос(ов). Всё равно завершить?`)) {
            return;
        }
    }

    showTestLoader('Проверяем ваши ответы...');

    try {
        const response = await fetch('/api/test/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                session_id: currentTestSession.id,
                answers: currentTestSession.userAnswers
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Не удалось сохранить результаты');
        }

        hideTestLoader();
        renderTestResults(data);

    } catch (error) {
        hideTestLoader();
        alert('Ошибка: ' + error.message);
    }
};

// ========== ЭКРАН РЕЗУЛЬТАТОВ ==========

function renderTestResults(data) {
    const container = document.getElementById('test-quiz-container');

    const scoreColor = data.score >= 80 ? '#4ecdc4' : data.score >= 50 ? '#fbbf24' : '#ef4444';
    const scoreEmoji = data.score >= 80 ? '🎉' : data.score >= 50 ? '👍' : '💪';

    container.innerHTML = `
        <div style="max-width: 800px; margin: 0 auto; padding: 40px 20px;">
            <!-- Заголовок результатов -->
            <div style="text-align: center; margin-bottom: 40px;">
                <div style="font-size: 64px; margin-bottom: 16px;">${scoreEmoji}</div>
                <h2 style="color: #f8fafc; margin: 0 0 8px 0;">Тест завершён!</h2>
                <p style="color: #94a3b8; margin: 0 0 24px 0;">${currentTestSession.topic}</p>
                
                <div style="
                    display: inline-block; background: #121826; border: 1px solid #24324a;
                    border-radius: 16px; padding: 24px 48px;
                ">
                    <div style="font-size: 48px; font-weight: 700; color: ${scoreColor}; margin-bottom: 8px;">
                        ${data.score}%
                    </div>
                    <div style="color: #cbd5e1; font-size: 16px;">
                        Правильных ответов: ${data.correct_answers} из ${data.total_questions}
                    </div>
                </div>
            </div>
            
            <!-- Разбор вопросов -->
            <h3 style="color: #f8fafc; margin-bottom: 20px;">Разбор ответов:</h3>
            
            ${data.results.map((q, idx) => {
                const isCorrect = q.is_correct;
                const borderColor = isCorrect ? '#4ecdc4' : (q.user_answer_index === null ? '#64748b' : '#ef4444');
                const statusEmoji = isCorrect ? '✓' : (q.user_answer_index === null ? '—' : '✕');
                const statusColor = isCorrect ? '#4ecdc4' : (q.user_answer_index === null ? '#64748b' : '#ef4444');
                
                return `
                    <div style="
                        background: #121826; border: 1px solid ${borderColor};
                        border-left: 4px solid ${borderColor};
                        border-radius: 12px; padding: 20px; margin-bottom: 16px;
                    ">
                        <div style="display: flex; gap: 12px; margin-bottom: 12px;">
                            <span style="
                                color: ${statusColor}; font-weight: 700; font-size: 20px;
                                flex-shrink: 0;
                            ">${statusEmoji}</span>
                            <div style="flex: 1;">
                                <div style="color: #f8fafc; font-weight: 600; margin-bottom: 8px;">
                                    ${idx + 1}. ${q.question_text}
                                </div>
                                
                                <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px;">
                                    ${q.options.map((opt, optIdx) => {
                                        const isUserAnswer = q.user_answer_index === optIdx;
                                        const isCorrectAnswer = q.correct_answer_index === optIdx;
                                        let style = 'background: #0f172a; color: #cbd5e1;';
                                        let marker = '';
                                        
                                        if (isCorrectAnswer) {
                                            style = 'background: rgba(78, 205, 196, 0.15); color: #4ecdc4; border: 1px solid #4ecdc4;';
                                            marker = ' ✓ Правильный ответ';
                                        } else if (isUserAnswer) {
                                            style = 'background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid #ef4444;';
                                            marker = ' ✕ Ваш ответ';
                                        }
                                        
                                        return `<div style="padding: 8px 12px; border-radius: 8px; font-size: 14px; ${style}">
                                            ${String.fromCharCode(65 + optIdx)}) ${opt}${marker}
                                        </div>`;
                                    }).join('')}
                                </div>
                                
                                ${!isCorrect ? `
                                    <div style="
                                        background: rgba(79, 140, 255, 0.1); border-left: 3px solid #4f8cff;
                                        padding: 10px 14px; border-radius: 6px; color: #cbd5e1; font-size: 14px;
                                    ">
                                        💡 <strong>Объяснение:</strong> ${q.explanation}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
            
            <!-- Кнопки действий -->
            <div style="display: flex; gap: 12px; justify-content: center; margin-top: 32px;">
                <button onclick="restartTest()" style="
                    background: #232d43; color: #e6eefc; border: none;
                    padding: 14px 28px; border-radius: 12px; cursor: pointer;
                    font-weight: 600; font-size: 15px;
                ">
                    🔄 Пройти ещё раз
                </button>
                <a href="/article/${currentTestSession.articleSlug}" style="
                    background: linear-gradient(135deg, #4f8cff, #4ecdc4);
                    color: #fff; border: none; padding: 14px 28px;
                    border-radius: 12px; text-decoration: none;
                    font-weight: 600; font-size: 15px; display: inline-flex;
                    align-items: center;
                ">
                    ← Вернуться к статье
                </a>
            </div>
        </div>
    `;
}

window.restartTest = function() {
    // Просто перезагружаем страницу, чтобы начать заново
    window.location.reload();
};