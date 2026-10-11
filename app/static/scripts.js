(function applySidebarStateEarly() {
  try {
    const userWantsClosed = localStorage.getItem('sidebarCollapsed') === 'true';
    const serverGaveClosed = document.body.classList.contains('sidebar-collapsed');

    // 1. Если сервер уже нарисовал закрытый сайдбар — доверяем серверу.
    if (serverGaveClosed) {
      // Но если пользователь явно хочет открытый (удалил ключ из localStorage),
      // можно раскомментировать следующую логику:
      // if (!userWantsClosed) { /* оставить как есть */ }
      document.body.classList.remove('js-prevent-animate');
      return;
    }

    // 2. Если сервер открыл, а пользователь хочет закрытый — применяем волю пользователя.
    if (userWantsClosed && !serverGaveClosed) {
      document.documentElement.classList.add('sidebar-collapsed');
      document.body.classList.add('sidebar-collapsed');
    }

    // 3. Разрешаем анимацию после того, как состояние определено.
    document.body.classList.remove('js-prevent-animate');
  } catch (e) {
    // Игнорируем ошибки localStorage
  }
})();

document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('toggleBtn');
  const sidebar = document.getElementById('sidebar');


  // --- АВТОМАТИЧЕСКОЕ ЗАКРЫТИЕ FLASH-МОССАЖЕЙ ---
  const container = document.querySelector('.flash-centerer .flash-container');
    if (!container) return;

    // Находим все текущие сообщения при загрузке страницы
    const toasts = container.querySelectorAll('.flash-toast');

    toasts.forEach(toast => {
        const closeBtn = toast.querySelector('.toast-close');
        
        // Функция удаления одного тоста
        const removeToast = () => {
            toast.classList.add('fade-out');
            setTimeout(() => {
                toast.remove();
            }, 300); // Ждем завершения анимации fadeOutUp
        };

        // Закрытие по крестику
        if (closeBtn) {
            closeBtn.addEventListener('click', removeToast);
        }
        
        // Авто-закрытие через 4 секунды
        setTimeout(removeToast, 4000);
    });


  // --- ЛОГИКА САЙДБАРА ---
  if (toggleBtn && sidebar && !window.sidebarInitialized) {
    window.sidebarInitialized = true;

    function syncSidebarState() {
      const userWantsClosed = localStorage.getItem('sidebarCollapsed') === 'true';

      // Применяем состояние из localStorage
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

      try {
        localStorage.setItem('sidebarCollapsed', nowCollapsed);
      } catch (e) {}

      // Синхронизируем классы на body/html с состоянием sidebar
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

    // Первоначальная синхронизация
    syncSidebarState();
  }

  const questionIcon = document.getElementById('questionIcon');
  const questionDropdown = document.getElementById('questionDropdown');

  if (questionIcon && questionDropdown) {
    questionIcon.addEventListener('click', (e) => {
      e.stopPropagation();
      questionDropdown.classList.toggle('show');
    });

    document.addEventListener('click', () => {
      questionDropdown.classList.remove('show');
    });
  }

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
            <div class="form-field">
              <label>Логин *</label>
              <input type="text" name="username" placeholder="ivanov123" required>
            </div>

            <div class="form-field">
              <label>Почта *</label>
              <input type="email" name="email" placeholder="student@example.com" required>
            </div>

            <div class="form-field">
              <label>Имя *</label>
              <input type="text" name="first_name" placeholder="Иван" required>
            </div>

            <div class="form-field">
              <label>Фамилия *</label>
              <input type="text" name="last_name" placeholder="Иванов" required>
            </div>

            <div class="form-field full">
              <label>Группа</label>
              <input type="text" name="group_name" placeholder="ИС-21 / ПР-31">
            </div>

            <div class="form-field">
              <label>Пароль *</label>
              <input type="password" name="password" placeholder="Минимум 6 символов" required>
            </div>

            <div class="form-field">
              <label>Повтор пароля *</label>
              <input type="password" name="confirm_password" placeholder="Повторите пароль" required>
            </div>
          </div>

          <button type="submit" class="auth-btn primary auth-submit">Зарегистрироваться</button>

          <p class="auth-switch">
            Уже есть аккаунт?
            <a href="#" onclick="openAuthModal('login'); return false;">Войти</a>
          </p>
        </form>
      `;
    } else {
      authTitle.textContent = 'Вход';
      authSubtitle.textContent = 'Войдите в аккаунт, чтобы продолжить';
      authBody.innerHTML = `
        <form method="post" action="/login" class="auth-form">
          <div class="form-field full">
            <label>Логин или почта</label>
            <input type="text" name="login" placeholder="Введите логин или email" required>
          </div>

          <div class="form-field full">
            <label>Пароль</label>
            <input type="password" name="password" placeholder="Введите пароль" required>
          </div>

          <button type="submit" class="auth-btn primary auth-submit">Войти</button>

          <p class="auth-switch">
            Нет аккаунта?
            <a href="#" onclick="openAuthModal('register'); return false;">Регистрация</a>
          </p>
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
    if (e.target === authModal) {
      window.closeAuthModal();
    }
  });

  if (authBody) {
    setAuthContent('login');
  }


      // --- ЗАГРУЗКА СТАТИСТИКИ ---
    const statElements = {
        total: document.getElementById('stat-total'),
        courses: document.getElementById('stat-courses'),
        modules: document.getElementById('stat-modules'),
        topics: document.getElementById('stat-topics'),
        articles: document.getElementById('stat-articles')
    };

    const tableAddedBody = document.getElementById('table-added-body');
    const tableUpdatedBody = document.getElementById('table-updated-body');

    async function loadDashboardData() {
        try {
            // Запрашиваем данные одновременно для скорости
            const [statsRes, addedRes] = await Promise.all([
                fetch('/api/dashboard/stats'),
                fetch('/api/articles/latest') 
            ]);

            if (!statsRes.ok || !addedRes.ok) throw new Error("Network response was not ok");

            const statsData = await statsRes.json();
            const addedData = await addedRes.json(); 

            // 1. Исправленная логика: заполняем карточки-счетчики через словарь соответствия
            const levelMap = {
                'courses': 'courses',
                'modules': 'modules', 
                'topics': 'topics',
                'articles': 'articles'
            };

            Object.keys(levelMap).forEach(key => {
                const element = statElements[key];
                const value = statsData.levels[levelMap[key]]; // Обращаемся строго по ключу levels.courses и т.д.
                
                if (element) {
                    element.textContent = value || 0;
                }
            });

            // Считаем "Всего" отдельно (сумма всех уровней)
            let sumLevels = 0;
            Object.values(statsData.levels).forEach(v => sumLevels += v);
            if (statElements.total) {
                statElements.total.textContent = statsData.total; // Или sumLevels, если хотите суммировать вручную
            }

            // Функция для очистки таблицы
            const clearTable = (tbody) => {
                tbody.innerHTML = '';
            };

            // Функция для рендера строки
            const renderRow = (article, dateField) => {
                const tr = document.createElement('tr');
                
                const titleTd = document.createElement('td');
                const link = document.createElement('a');
                link.href = '/article/' + article.slug;
                link.textContent = article.title;
                titleTd.appendChild(link);

                const typeTd = document.createElement('td');
                typeTd.textContent = article.level_name;

                const dateTd = document.createElement('td');
                dateTd.textContent = article[dateField];

                tr.appendChild(titleTd);
                tr.appendChild(typeTd);
                tr.appendChild(dateTd);
                return tr;
            };

            // 2. Заполняем таблицу "Последние добавленные"
            clearTable(tableAddedBody);
            if (addedData.length > 0) {
                addedData.forEach(article => {
                    tableAddedBody.appendChild(renderRow(article, 'created_at'));
                });
            } else {
                tableAddedBody.innerHTML = '<tr><td colspan="3"><em>Нет данных</em></td></tr>';
            }

            // 3. Заполняем таблицу "Последние обновленные"
            clearTable(tableUpdatedBody);
            if (statsData.latest_updated.length > 0) {
                statsData.latest_updated.forEach(article => {
                    tableUpdatedBody.appendChild(renderRow(article, 'updated_at'));
                });
            } else {
                tableUpdatedBody.innerHTML = '<tr><td colspan="3"><em>Нет данных</em></td></tr>';
            }

        } catch (error) {
            console.error('Ошибка при загрузке статистики:', error);
            // Показываем пользователю ошибку вместо лоадеров
            if (tableAddedBody && tableUpdatedBody) {
                tableAddedBody.innerHTML = '<tr><td colspan="3"><em>Ошибка загрузки</em></td></tr>';
                tableUpdatedBody.innerHTML = '<tr><td colspan="3"><em>Ошибка загрузки</em></td></tr>';
            }
        }
    }

    // Запуск загрузки статистики
    loadDashboardData();
});

class TreeMenu {
  constructor(container) {
    this.container = container;
    this.openNodes = JSON.parse(localStorage.getItem('openNodes') || '[]');
  }

getLevelIcon(level) {
    // Мы возвращаем HTML-тег <i>, который будет стилизован вашим *существующим* CSS.
    if (level === 0) {
        return '<i class="fa-solid fa-book"></i>';
    } else if (level === 3) {
        return '<i class="fa-solid fa-file"></i>';
    } else {
        // Для уровней 1 и 2 (Модуль и Тема) используем папку
        return '<i class="fa-solid fa-folder"></i>';
    }
}

getLevelName(level) {
    if (level === 0) {
        return 'Курс';
    } else if (level === 1) {
        return 'Модуль'; // Возвращаем "Модуль" для уровня 1
    } else if (level === 2) {
        return 'Тема';   // Возвращаем "Тема" для уровня 2
    } else if (level === 3) {
        return 'Статья';
    }
    return ''; // Пустой результат для неизвестных уровней
}




  renderTree(data) {
    this.container.innerHTML = '<ul id="tree-navigation">' + this.buildNode(data) + '</ul>';
    this.attachEvents();
  }

buildNode(nodes) {
    if (!Array.isArray(nodes)) nodes = [nodes];
    let html = '';

    for (const node of nodes) {
        // Внутри цикла for (const node of nodes)
        const icon = this.getLevelIcon(node.level);
        const levelName = this.getLevelName(node.level);

        let draftIndicator = '';
        if (window.CURRENT_USER_IS_ADMIN && node.has_draft) {
            // Используем маленькую точку И иконку карандаша для наглядности
            draftIndicator = '<span class="tree-draft-indicator" title="Есть несохраненный черновик"><i class="fa-solid fa-pen"></i></span>';
        }

        const badge = node.children_count > 0 ? `<span class="badge">${node.children_count}</span>` : '';
        const chevron = (node.children && node.children.length) ? '<span class="chevron"></span>' : '';
        const isOpen = this.openNodes.includes(node.id);

        html += `
          <li class="tree-node level-${node.level} ${isOpen ? 'open' : ''}" data-id="${node.id}">
            <div class="node-header">
              <span class="node-icon">${icon}</span>
              <span class="level-label">${levelName}</span>
              <a href="/article/${node.slug}" class="node-link">
                ${node.title}
                ${draftIndicator}
              </a>
              ${chevron}
              ${badge}
            </div>
            ${node.children && node.children.length ? `<ul class="children ${isOpen ? 'show' : ''}">${this.buildNode(node.children)}</ul>` : ''}
          </li>`;
    }
    return html;
}

  attachEvents() {
    this.container.querySelectorAll('.node-header').forEach(header => {
      header.addEventListener('click', (e) => {
        if (e.target.closest('.node-link')) return;
        const node = header.closest('.tree-node');
        if (node) this.toggleNode(node);
      });
    });

    this.container.querySelectorAll('.node-link').forEach(link => {
      link.addEventListener('click', (e) => e.stopPropagation());
    });
  }

  

  toggleNode(node) {
    const nodeId = parseInt(node.dataset.id, 10);
    const isOpen = node.classList.contains('open');
    const children = node.querySelector(':scope > .children');

    node.classList.toggle('open');
    if (children) children.classList.toggle('show');

    const chevron = node.querySelector(':scope > .node-header .chevron');
    if (chevron) chevron.classList.toggle('open');

    if (isOpen) {
      this.openNodes = this.openNodes.filter(id => id != nodeId);
    } else {
      this.openNodes.push(nodeId);
    }

    try {
      localStorage.setItem('openNodes', JSON.stringify(this.openNodes));
    } catch (e) {}
  }
}

function initTreeMenu() {
  if (window.treeData && window.treeData.length) {
    const treeNav = document.getElementById('tree-navigation') || document.querySelector('.sidebar ul');
    if (treeNav) {
      const treeMenu = new TreeMenu(treeNav);
      treeMenu.renderTree(window.treeData);
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTreeMenu);
} else {
  initTreeMenu();
}

document.addEventListener('DOMContentLoaded', function() {
  const textarea = document.getElementById('content-editor');

  if (!textarea || typeof EasyMDE === 'undefined') return;

  const editor = new EasyMDE({
    element: textarea,
    spellChecker: false,
    autofocus: true,
    autosave: {
      enabled: true,
      uniqueId: 'kb-editor-' + window.location.pathname 
    },
    status: ['autosave', 'lines', 'words', 'cursor'],
    toolbar: [

      {
                name: "custom_undo",
                action: function(editorInstance) { 
                    editorInstance.codemirror.execCommand("undo"); 
                    updateNavButtons(); // Обновляем состояние после действия
                },
                className: "fa fa-rotate-left custom-history-btn", 
                title: "Отменить действие"
            },
            {
                name: "custom_redo",
                action: function(editorInstance) { 
                    editorInstance.codemirror.execCommand("redo"); 
                    updateNavButtons();
                },
                className: "fa fa-rotate-right custom-history-btn",
                title: "Вернуть действие"
            },
            "|", // Разделитель
      {
        name: 'h1',
        action: function(editor) {
          editor.codemirror.replaceSelection('# ');
          editor.codemirror.focus();
        },
        className: 'fa fa-heading',
        title: 'H1 — Заголовок 1'
      },
      {
        name: 'h2',
        action: function(editor) {
          editor.codemirror.replaceSelection('## ');
          editor.codemirror.focus();
        },
        className: 'fa fa-heading',
        title: 'H2 — Заголовок 2'
      },
      {
        name: 'h3',
        action: function(editor) {
          editor.codemirror.replaceSelection('### ');
          editor.codemirror.focus();
        },
        className: 'fa fa-heading',
        title: 'H3 — Заголовок 3'
      },
      {
        name: 'h4',
        action: function(editor) {
          editor.codemirror.replaceSelection('#### ');
          editor.codemirror.focus();
        },
        className: 'fa fa-heading',
        title: 'H4 — Заголовок 4'
      },
      '|',
      'bold',
      'italic',
      'strikethrough',
      '|',
      'quote',
      'unordered-list',
      'ordered-list',
      '|',
      'link',
      {
        name: 'upload-image',
        action: function(editorInstance) {
          const input = document.createElement('input');
          input.type = 'file';
          input.accept = 'image/*';

          input.onchange = async function() {
            const file = input.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('upload', file);

            try {
              const response = await fetch('/upload-image', {
                method: 'POST',
                body: formData
              });

              const data = await response.json();

              if (data.default) {
                editorInstance.codemirror.replaceSelection(`![${file.name}](${data.default})`);
              } else {
                alert('Не удалось загрузить изображение');
              }
            } catch (e) {
              alert('Ошибка загрузки изображения');
            }
          };

          input.click();
        },
        className: 'fa fa-image',
        title: 'Загрузить изображение'
      },
      '|',
      'table',
      'code',
      'horizontal-rule',
      '|',
      'preview',
      'side-by-side',
      'fullscreen'
    ]
  });
  
  
  window.articleEditor = editor;

    // Автосохранение черновиков на сервер (Вариант 2 из обсуждения)
  const pathname = window.location.pathname;
  
  // Работаем только на странице редактирования
  if (pathname.startsWith('/edit_article/')) {
    let saveTimer = null;

    function sendDraft() {
      const editorText = window.articleEditor.value();
      const slug = pathname.split('/').pop();

      fetch('/api/draft/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          slug: slug,
          content: editorText
        })
      })
      .then(response => response.json())
      .then(data => {
        console.log('[DRAFT] Auto-saved to server at', new Date().toLocaleTimeString());
      })
      .catch(err => {
        console.error('[DRAFT] Failed to save draft:', err);
      });
    }

    // Сохраняем каждые 60 секунд И перед закрытием вкладки
    saveTimer = setInterval(sendDraft, 60000);
    
    window.addEventListener('beforeunload', () => {
      clearInterval(saveTimer);
      sendDraft(); // Попытка финального сохранения
    });
  }


function sendDraftToServer() {
    const content = editor.value();
    const path = window.location.pathname; // /edit_article/my-slug
    const slug = path.split('/').pop(); 

    fetch(`/save-draft/${slug}`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': '{{ csrf_token() }}' // Если используешь защиту форм
        },
        body: `title=${encodeURIComponent(document.querySelector('[name="title"]').value)}&content=${encodeURIComponent(content)}&submit_type=draft`
    })
    .then(r => r.json())
    .then(data => console.log('[DRAFT] Auto-saved to server'))
    .catch(err => console.error('[DRAFT] Failed:', err));
}





});


