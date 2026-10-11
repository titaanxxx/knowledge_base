// ===========================================
// UI: Сайдбар, модалки, toast-уведомления
// ===========================================

(function applySidebarStateEarly() {
  try {
    const userWantsClosed = localStorage.getItem('sidebarCollapsed') === 'true';
    const serverGaveClosed = document.body.classList.contains('sidebar-collapsed');

    if (serverGaveClosed) {
      document.body.classList.remove('js-prevent-animate');
      return;
    }

    if (userWantsClosed && !serverGaveClosed) {
      document.documentElement.classList.add('sidebar-collapsed');
      document.body.classList.add('sidebar-collapsed');
    }

    document.body.classList.remove('js-prevent-animate');
  } catch (e) {}
})();

document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('toggleBtn');
  const sidebar = document.getElementById('sidebar');

  // Toast-уведомления
  const container = document.querySelector('.flash-centerer .flash-container');
  if (container) {
    const toasts = container.querySelectorAll('.flash-toast');
    toasts.forEach(toast => {
      const closeBtn = toast.querySelector('.toast-close');
      const removeToast = () => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
      };
      if (closeBtn) closeBtn.addEventListener('click', removeToast);
      setTimeout(removeToast, 4000);
    });
  }

  // Сайдбар
  if (toggleBtn && sidebar && !window.sidebarInitialized) {
    window.sidebarInitialized = true;

    function syncSidebarState() {
      const userWantsClosed = localStorage.getItem('sidebarCollapsed') === 'true';
      if (userWantsClosed) {
        sidebar.classList.add('collapsed');
        document.body.classList.add('sidebar-collapsed');
        document.documentElement.classList.add('sidebar-collapsed');
      } else {
        sidebar.classList.remove('collapsed');
        document.body.classList.remove('sidebar-collapsed');
        document.documentElement.classList.remove('sidebar-collapsed');
      }
      syncSidebarButton();
    }

    function syncSidebarButton() {
      const collapsed = sidebar.classList.contains('collapsed');
      toggleBtn.innerHTML = collapsed ? '→' : '←';
    }

    function toggleSidebar() {
      sidebar.classList.toggle('collapsed');
      const nowCollapsed = sidebar.classList.contains('collapsed');
      try { localStorage.setItem('sidebarCollapsed', nowCollapsed); } catch (e) {}
      if (nowCollapsed) {
        document.body.classList.add('sidebar-collapsed');
        document.documentElement.classList.add('sidebar-collapsed');
      } else {
        document.body.classList.remove('sidebar-collapsed');
        document.documentElement.classList.remove('sidebar-collapsed');
      }
      syncSidebarButton();
    }

    toggleBtn.addEventListener('click', toggleSidebar);
    syncSidebarState();
  }

  // Вопрос-иконка
  const questionIcon = document.getElementById('questionIcon');
  const questionDropdown = document.getElementById('questionDropdown');
  if (questionIcon && questionDropdown) {
    questionIcon.addEventListener('click', (e) => {
      e.stopPropagation();
      questionDropdown.classList.toggle('show');
    });
    document.addEventListener('click', () => questionDropdown.classList.remove('show'));
  }

  // Модалка "О базе знаний"
  window.showAbout = function() {
    const modal = document.getElementById('aboutModal');
    if (modal) modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  };
  window.closeAbout = function() {
    const modal = document.getElementById('aboutModal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
  };

  // Модалка авторизации
  const authModal = document.getElementById('authModal');
  const authBody = document.getElementById('authBody');
  const authTitle = document.getElementById('authTitle');
  const authSubtitle = document.getElementById('authSubtitle');

  function setAuthContent(mode) {
    if (!authModal || !authBody || !authTitle || !authSubtitle) return;

    if (mode === 'register') {
      authTitle.textContent = 'Регистрация';
      authSubtitle.textContent = 'Создайте аккаунт для доступа к базе знаний';
      authBody.innerHTML = `
        <form method="post" action="/register" class="auth-form">
          <div class="form-grid">
            <div class="form-field"><label>Логин *</label><input type="text" name="username" placeholder="ivanov123" required></div>
            <div class="form-field"><label>Почта *</label><input type="email" name="email" placeholder="student@example.com" required></div>
            <div class="form-field"><label>Имя *</label><input type="text" name="first_name" placeholder="Иван" required></div>
            <div class="form-field"><label>Фамилия *</label><input type="text" name="last_name" placeholder="Иванов" required></div>
            <div class="form-field full"><label>Группа</label><input type="text" name="group_name" placeholder="ИС-21 / ПР-31"></div>
            <div class="form-field"><label>Пароль *</label><input type="password" name="password" placeholder="Минимум 6 символов" required></div>
            <div class="form-field"><label>Повтор пароля *</label><input type="password" name="confirm_password" placeholder="Повторите пароль" required></div>
          </div>
          <button type="submit" class="auth-btn primary auth-submit">Зарегистрироваться</button>
          <p class="auth-switch">Уже есть аккаунт? <a href="#" onclick="openAuthModal('login'); return false;">Войти</a></p>
        </form>
      `;
    } else {
      authTitle.textContent = 'Вход';
      authSubtitle.textContent = 'Войдите в аккаунт, чтобы продолжить';
      authBody.innerHTML = `
        <form method="post" action="/login" class="auth-form">
          <div class="form-field full"><label>Логин или почта</label><input type="text" name="login" placeholder="Введите логин или email" required></div>
          <div class="form-field full"><label>Пароль</label><input type="password" name="password" placeholder="Введите пароль" required></div>
          <button type="submit" class="auth-btn primary auth-submit">Войти</button>
          <p class="auth-switch">Нет аккаунта? <a href="#" onclick="openAuthModal('register'); return false;">Регистрация</a></p>
        </form>
      `;
    }
  }

  window.openAuthModal = function(mode = 'login') {
    if (!authModal) return;
    authModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    setAuthContent(mode);
  };
  window.closeAuthModal = function() {
    if (!authModal) return;
    authModal.style.display = 'none';
    document.body.style.overflow = '';
  };
  document.addEventListener('click', (e) => {
    if (e.target === authModal) window.closeAuthModal();
  });
  if (authBody) setAuthContent('login');

  // ИИ-помощник
  window.openAiQuestionModal = function() {
    document.getElementById('ai-question-modal').style.display = 'flex';
    document.getElementById('ai-question-text').focus();
  };
  window.closeAiQuestionModal = function() {
    document.getElementById('ai-question-modal').style.display = 'none';
    document.getElementById('ai-loading').style.display = 'none';
    document.getElementById('ai-answer').style.display = 'none';
    document.getElementById('ai-question-text').value = '';
  };
  window.submitAiQuestion = async function() {
    const question = document.getElementById('ai-question-text').value.trim();
    if (!question) { alert('Введите вопрос!'); return; }
    document.getElementById('ai-loading').style.display = 'block';
    document.getElementById('ai-answer').style.display = 'none';
    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data = await response.json();
      if (data.error) { alert('Ошибка: ' + data.error); return; }
      document.getElementById('ai-loading').style.display = 'none';
      document.getElementById('ai-answer').style.display = 'block';
      const htmlAnswer = marked.parse(data.answer);
      document.getElementById('ai-answer-text').innerHTML = htmlAnswer;
      const sourcesList = document.getElementById('sources-list');
      sourcesList.innerHTML = '';
      data.sources.forEach(source => {
        const li = document.createElement('li');
        li.innerHTML = `<a href="/article/${source.slug}">${source.title}<span class="relevance-badge">${source.relevance}% совпадение</span></a>`;
        sourcesList.appendChild(li);
      });
    } catch (error) {
      document.getElementById('ai-loading').style.display = 'none';
      alert('Ошибка соединения: ' + error.message);
    }
  };
  window.rateAnswer = function(helpful) {
    alert('Спасибо за оценку! (функционал в разработке)');
    closeAiQuestionModal();
  };
  window.onclick = function(event) {
    const modal = document.getElementById('ai-question-modal');
    if (event.target === modal) closeAiQuestionModal();
  };
});