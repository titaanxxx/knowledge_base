// ===========================================
// TreeMenu: Дерево навигации
// ===========================================

class TreeMenu {
  constructor(container) {
    this.container = container;
    this.openNodes = JSON.parse(localStorage.getItem('openNodes') || '[]');
  }

  getLevelIcon(level) {
    if (level === 0) return '<i class="fa-solid fa-book"></i>';
    else if (level === 3) return '<i class="fa-solid fa-file"></i>';
    else return '<i class="fa-solid fa-folder"></i>';
  }

  getLevelName(level) {
    if (level === 0) return 'Курс';
    else if (level === 1) return 'Модуль';
    else if (level === 2) return 'Тема';
    else if (level === 3) return 'Статья';
    return '';
  }

  renderTree(data) {
    this.container.innerHTML = '<ul id="tree-navigation">' + this.buildNode(data) + '</ul>';
    this.attachEvents();
  }

  buildNode(nodes) {
    if (!Array.isArray(nodes)) nodes = [nodes];
    let html = '';
    for (const node of nodes) {
      const icon = this.getLevelIcon(node.level);
      const levelName = this.getLevelName(node.level);
      let draftIndicator = '';
      if (window.CURRENT_USER_IS_ADMIN && node.has_draft) {
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
            <a href="/article/${node.slug}" class="node-link">${node.title}${draftIndicator}</a>
            ${chevron}${badge}
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
    try { localStorage.setItem('openNodes', JSON.stringify(this.openNodes)); } catch (e) {}
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