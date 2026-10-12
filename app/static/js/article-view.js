// ===========================================
// Article View: Нумерация строк в статьях при чтении
// ===========================================

(function() {
  function addLineNumbersToArticles() {
    console.log("🚀 Запуск нумерации строк в статьях...");

    // Ищем контейнер статьи по нескольким возможным классам (выбери тот, который у тебя)
    const articleContainer = document.querySelector('.article-text') ||
                             document.querySelector('.article-content') ||
                             document.querySelector('.content-inner') ||
                             document.body; // Если ничего не нашли, ищем по всей странице

    console.log("📦 Найденный контейнер имеет классы:", articleContainer.className);

    // Ищем все <pre> внутри этого контейнера
    const codeBlocks = articleContainer.querySelectorAll('pre');
    console.log(`🔍 Найдено блоков кода (<pre>): ${codeBlocks.length}`);

    if (codeBlocks.length === 0) {
        console.warn("⚠️ Блоки <pre> не найдены! Проверь, есть ли код в статье.");
        return;
    }

    codeBlocks.forEach((preBlock) => {
      // Берем текст из <code> внутри <pre>, или из самого <pre>, если <code> нет
      const codeElement = preBlock.querySelector('code') || preBlock;
      const text = codeElement.textContent;

      const lines = text.split('\n');

      // Убираем последнюю пустую строку, если она есть
      if (lines.length > 0 && lines[lines.length - 1].trim() === '') {
        lines.pop();
      }

      const numberedHtml = lines.map((line, index) => {
        const escapedLine = line
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;');

        return `<div class="numbered-code-line">
                  <span class="code-line-number">${index + 1}</span>
                  <span class="code-line-text">${escapedLine || ' '}</span>
                </div>`;
      }).join('');

      const wrapper = document.createElement('div');
      wrapper.className = 'numbered-code-block';
      wrapper.innerHTML = numberedHtml;

      // Заменяем исходный <pre> на наш красивый нумерованный блок
      preBlock.replaceWith(wrapper);
    });

    console.log("✅ Нумерация строк успешно применена!");
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addLineNumbersToArticles);
  } else {
    addLineNumbersToArticles();
  }
})();