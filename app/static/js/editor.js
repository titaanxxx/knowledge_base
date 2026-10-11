// ===========================================
// Editor: EasyMDE + Dashboard
// ===========================================

document.addEventListener('DOMContentLoaded', function() {
  // Загрузка статистики
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
      const [statsRes, addedRes] = await Promise.all([
        fetch('/api/dashboard/stats'),
        fetch('/api/articles/latest')
      ]);
      if (!statsRes.ok || !addedRes.ok) throw new Error("Network response was not ok");
      const statsData = await statsRes.json();
      const addedData = await addedRes.json();
      const levelMap = { 'courses': 'courses', 'modules': 'modules', 'topics': 'topics', 'articles': 'articles' };
      Object.keys(levelMap).forEach(key => {
        const element = statElements[key];
        const value = statsData.levels[levelMap[key]];
        if (element) element.textContent = value || 0;
      });
      let sumLevels = 0;
      Object.values(statsData.levels).forEach(v => sumLevels += v);
      if (statElements.total) statElements.total.textContent = statsData.total;
      const clearTable = (tbody) => { tbody.innerHTML = ''; };
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
      clearTable(tableAddedBody);
      if (addedData.length > 0) {
        addedData.forEach(article => tableAddedBody.appendChild(renderRow(article, 'created_at')));
      } else {
        tableAddedBody.innerHTML = '<tr><td colspan="3"><em>Нет данных</em></td></tr>';
      }
      clearTable(tableUpdatedBody);
      if (statsData.latest_updated.length > 0) {
        statsData.latest_updated.forEach(article => tableUpdatedBody.appendChild(renderRow(article, 'updated_at')));
      } else {
        tableUpdatedBody.innerHTML = '<tr><td colspan="3"><em>Нет данных</em></td></tr>';
      }
    } catch (error) {
      console.error('Ошибка при загрузке статистики:', error);
      if (tableAddedBody && tableUpdatedBody) {
        tableAddedBody.innerHTML = '<tr><td colspan="3"><em>Ошибка загрузки</em></td></tr>';
        tableUpdatedBody.innerHTML = '<tr><td colspan="3"><em>Ошибка загрузки</em></td></tr>';
      }
    }
  }
  loadDashboardData();

  // EasyMDE редактор
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
        },
        className: "fa fa-rotate-left custom-history-btn",
        title: "Отменить действие"
      },
      {
        name: "custom_redo",
        action: function(editorInstance) {
          editorInstance.codemirror.execCommand("redo");
        },
        className: "fa fa-rotate-right custom-history-btn",
        title: "Вернуть действие"
      },
      "|",
      { name: 'h1', action: function(editor) { editor.codemirror.replaceSelection('# '); editor.codemirror.focus(); }, className: 'fa fa-heading', title: 'H1' },
      { name: 'h2', action: function(editor) { editor.codemirror.replaceSelection('## '); editor.codemirror.focus(); }, className: 'fa fa-heading', title: 'H2' },
      { name: 'h3', action: function(editor) { editor.codemirror.replaceSelection('### '); editor.codemirror.focus(); }, className: 'fa fa-heading', title: 'H3' },
      { name: 'h4', action: function(editor) { editor.codemirror.replaceSelection('#### '); editor.codemirror.focus(); }, className: 'fa fa-heading', title: 'H4' },
      '|', 'bold', 'italic', 'strikethrough', '|', 'quote', 'unordered-list', 'ordered-list', '|', 'link',
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
              const response = await fetch('/upload-image', { method: 'POST', body: formData });
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
      '|', 'table', 'code', 'horizontal-rule', '|', 'preview', 'side-by-side', 'fullscreen'
    ]
  });

  window.articleEditor = editor;

  // Автосохранение черновиков
  const pathname = window.location.pathname;
  if (pathname.startsWith('/admin/edit_article/')) {
    let saveTimer = null;
    function sendDraft() {
      const editorText = window.articleEditor.value();
      const slug = pathname.split('/').pop();
      fetch('/api/draft/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ slug: slug, content: editorText })
      })
      .then(response => response.json())
      .then(data => console.log('[DRAFT] Auto-saved to server at', new Date().toLocaleTimeString()))
      .catch(err => console.error('[DRAFT] Failed to save draft:', err));
    }
    saveTimer = setInterval(sendDraft, 60000);
    window.addEventListener('beforeunload', () => {
      clearInterval(saveTimer);
      sendDraft();
    });
  }
});