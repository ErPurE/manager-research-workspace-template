/**
 * 科研管理仪表板 - 前端逻辑
 */

const API_BASE = '';
const KIND_LABELS = {
    idea: '灵感',
    task: '任务',
    guidance: '导师消息',
    note: '笔记',
    freeform: '自由输入',
    file_edit_review: '文件复查'
};
const STATUS_LABELS = {
    pending: '待处理',
    failed: '失败',
    cancelled: '已取消',
    processed: '已处理'
};
const BODY_PLACEHOLDERS = {
    idea: '记录突然想到的研究想法、可能的图、潜在路线或问题。',
    task: '记录新任务、截止时间、来源和你希望 Agent 下次怎么拆解。',
    guidance: '原样记录导师刚说的话、要求、口头反馈或需要回复的点。',
    note: '记录一段待整理笔记，Agent 下次会判断归档位置。',
    freeform: '先原样记下来，Agent 下次启动时会接管整理。'
};

let currentSection = 'dashboard';
let currentCaptureKind = 'idea';
let editingInboxId = null;
let inboxItemsById = new Map();
let currentFile = null;
let agentProfilesData = { active_profile_id: '', profiles: [] };
let lastAgentRunId = '';
let appUpdateState = { latest_version: '', downloaded_version: '' };

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initCaptureForm();
    initFileModal();
    initAgentPanel();
    initAppPanel();
    const initialSection = getSectionFromHash();
    if (initialSection && document.getElementById(initialSection)) {
        showSection(initialSection);
    } else {
        loadDashboard();
    }
});

// ===== 导航 =====
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const section = item.dataset.section;
            showSection(section);
        });
    });
}

function showSection(sectionId) {
    currentSection = sectionId;
    if (window.location.hash !== `#${sectionId}`) {
        history.replaceState(null, '', `#${sectionId}`);
    }

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionId);
    });

    document.querySelectorAll('.section').forEach(section => {
        section.classList.toggle('active', section.id === sectionId);
    });

    switch (sectionId) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'inbox':
            loadInbox();
            break;
        case 'agent':
            loadAgentProfiles();
            loadAppInfo();
            break;
        case 'ideas':
            loadFiles('ideas', 'ideas-grid');
            break;
        case 'tasks':
            loadTodos();
            break;
        case 'guidance':
            loadFiles('guidance', 'guidance-grid');
            break;
        case 'notes':
            loadFiles('notes', 'notes-grid');
            break;
    }
}

function getSectionFromHash() {
    return window.location.hash.replace('#', '').trim();
}

// ===== 加载数据 =====
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/api/structure`);
        const data = await response.json();

        setText('ideas-count', data.ideas || 0);
        setText('tasks-count', data.tasks || 0);
        setText('guidance-count', data.guidance || 0);
        setText('notes-count', data.notes || 0);
        setText('inbox-count', data.inbox_pending || 0);
        setText('inbox-pending-count', data.inbox_pending || 0);
        setText('inbox-failed-count', data.inbox_failed || 0);
        setText('inbox-cancelled-count', data.inbox_cancelled || 0);
        await loadInbox();
    } catch (error) {
        console.error('加载仪表板失败:', error);
    }
}

async function loadTodos() {
    const board = document.getElementById('tasks-board');
    if (!board) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/todos`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '加载失败');
        }
        renderTodos(data.items || []);
    } catch (error) {
        console.error('加载待办失败:', error);
        board.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">ERR</div>
                <div class="empty-state-text">待办加载失败，请检查 tasks/todo.json</div>
            </div>
        `;
    }
}

function renderTodos(items) {
    const board = document.getElementById('tasks-board');
    const activeItems = items.filter(item => !['done', 'cancelled'].includes(item.status));
    const doneItems = items.filter(item => item.status === 'done');
    const groups = [
        ['today', '今天先做', '现在最该推进的任务'],
        ['week', '本周推进', '近期科研主线'],
        ['later', '后续收口', '有明确方向但不抢今天'],
        ['backlog', '待排期', '先记住，之后安排'],
        ['admin', '行政杂务', '财务、报销、专利等']
    ];

    const summary = {
        total: activeItems.length,
        urgent: activeItems.filter(item => Number(item.priority) === 3).length,
        doing: activeItems.filter(item => item.status === 'in_progress').length,
        blocked: activeItems.filter(item => item.status === 'blocked').length,
        done: doneItems.length
    };

    board.innerHTML = `
        <div class="todo-summary">
            <span><strong>${summary.total}</strong> 未完成</span>
            <span><strong>${summary.urgent}</strong> 高优先级</span>
            <span><strong>${summary.doing}</strong> 进行中</span>
            <span><strong>${summary.blocked}</strong> 阻塞</span>
            <span><strong>${summary.done}</strong> 已完成</span>
        </div>
        <div class="todo-columns">
            ${groups.map(([group, title, subtitle]) => renderTodoGroup(group, title, subtitle, activeItems)).join('')}
        </div>
        ${renderCompletedTodos(doneItems)}
    `;

    board.querySelectorAll('[data-todo-toggle]').forEach(button => {
        button.addEventListener('click', () => {
            toggleTodoStatus(button.dataset.todoToggle, button.dataset.nextStatus);
        });
    });
    board.querySelectorAll('[data-checklist-toggle]').forEach(button => {
        button.addEventListener('click', () => {
            toggleChecklistItem(
                button.dataset.checklistToggle,
                Number(button.dataset.checklistIndex),
                button.dataset.checklistDone === 'true'
            );
        });
    });
}

function renderCompletedTodos(items) {
    const doneItems = [...items].sort((a, b) => {
        const dateDiff = String(b.updated_at || '').localeCompare(String(a.updated_at || ''));
        if (dateDiff !== 0) {
            return dateDiff;
        }
        return String(a.title || '').localeCompare(String(b.title || ''), 'zh-CN');
    });

    return `
        <section class="completed-todos">
            <div class="completed-todos-header">
                <div>
                    <h2>已完成，可撤销</h2>
                    <p>误点完成后，从这里恢复到完成前状态</p>
                </div>
                <span>${doneItems.length}</span>
            </div>
            <div class="completed-todos-list">
                ${doneItems.length ? doneItems.map(renderTodoItem).join('') : `
                    <div class="todo-empty">暂无已完成任务</div>
                `}
            </div>
        </section>
    `;
}

function renderTodoGroup(group, title, subtitle, items) {
    const groupItems = items
        .filter(item => item.group === group || (group === 'admin' && item.area === 'admin'))
        .sort(compareTodos);

    return `
        <section class="todo-column">
            <div class="todo-column-header">
                <div>
                    <h2>${escapeHtml(title)}</h2>
                    <p>${escapeHtml(subtitle)}</p>
                </div>
                <span>${groupItems.length}</span>
            </div>
            <div class="todo-list">
                ${groupItems.length ? groupItems.map(renderTodoItem).join('') : `
                    <div class="todo-empty">暂无任务</div>
                `}
            </div>
        </section>
    `;
}

function renderTodoItem(item) {
    const status = item.status || 'todo';
    const nextStatus = status === 'done' ? (item.previous_status || 'todo') : 'done';
    const priority = Number(item.priority || 1);
    const tags = Array.isArray(item.tags) ? item.tags : [];
    const checklist = normalizeChecklist(item.checklist);
    const toggleTitle = status === 'done' ? '撤销完成' : '标记为完成';
    return `
        <article class="todo-item priority-${priority} status-${escapeHtml(status)}">
            <button class="todo-check" data-todo-toggle="${escapeHtml(item.id)}" data-next-status="${escapeHtml(nextStatus)}" title="${toggleTitle}" aria-label="${toggleTitle}">
                ${status === 'done' ? '✓' : ''}
            </button>
            <div class="todo-main">
                <div class="todo-title-row">
                    <h3>${escapeHtml(item.title)}</h3>
                    <span class="todo-status">${formatTodoStatus(status)}</span>
                </div>
                <div class="todo-meta">
                    ${item.project ? `<span>${escapeHtml(item.project)}</span>` : ''}
                    ${item.due_label ? `<span>${escapeHtml(item.due_label)}</span>` : ''}
                    <span>${formatPriority(priority)}</span>
                </div>
                ${item.note ? `<p class="todo-note">${escapeHtml(item.note)}</p>` : ''}
                ${checklist.length ? `
                    <ul class="todo-checklist">
                        ${checklist.map((entry, index) => renderChecklistItem(item.id, entry, index)).join('')}
                    </ul>
                ` : ''}
                ${tags.length ? `<div class="todo-tags">${tags.map(tag => `<span>${escapeHtml(tag)}</span>`).join('')}</div>` : ''}
            </div>
        </article>
    `;
}

function normalizeChecklist(checklist) {
    if (!Array.isArray(checklist)) {
        return [];
    }
    return checklist
        .map(entry => {
            if (entry && typeof entry === 'object') {
                return {
                    text: String(entry.text || entry.title || '').trim(),
                    done: Boolean(entry.done)
                };
            }
            return {
                text: String(entry || '').trim(),
                done: false
            };
        })
        .filter(entry => entry.text);
}

function renderChecklistItem(todoId, entry, index) {
    const nextDone = !entry.done;
    const title = entry.done ? '标记为未完成' : '标记为已完成';
    return `
        <li class="todo-checklist-item ${entry.done ? 'is-done' : ''}">
            <button class="subtask-check"
                data-checklist-toggle="${escapeHtml(todoId)}"
                data-checklist-index="${index}"
                data-checklist-done="${nextDone}"
                title="${title}"
                aria-label="${title}">
                ${entry.done ? '✓' : ''}
            </button>
            <span>${escapeHtml(entry.text)}</span>
        </li>
    `;
}

async function toggleTodoStatus(todoId, nextStatus) {
    try {
        const response = await fetch(`${API_BASE}/api/todos/${encodeURIComponent(todoId)}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: nextStatus })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '更新失败');
        }
        await loadDashboard();
        if (currentSection === 'tasks') {
            await loadTodos();
        }
    } catch (error) {
        console.error('更新任务失败:', error);
        alert(`更新任务失败：${error.message}`);
    }
}

async function toggleChecklistItem(todoId, checklistIndex, checklistDone) {
    try {
        const response = await fetch(`${API_BASE}/api/todos/${encodeURIComponent(todoId)}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                checklist_index: checklistIndex,
                checklist_done: checklistDone
            })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '更新失败');
        }
        await loadDashboard();
        if (currentSection === 'tasks') {
            await loadTodos();
        }
    } catch (error) {
        console.error('更新子任务失败:', error);
        alert(`更新子任务失败：${error.message}`);
    }
}

function compareTodos(a, b) {
    const priorityDiff = Number(b.priority || 1) - Number(a.priority || 1);
    if (priorityDiff !== 0) {
        return priorityDiff;
    }
    const statusOrder = { in_progress: 0, blocked: 1, waiting: 2, todo: 3, paused: 4 };
    const statusDiff = (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9);
    if (statusDiff !== 0) {
        return statusDiff;
    }
    return String(a.title || '').localeCompare(String(b.title || ''), 'zh-CN');
}

function formatTodoStatus(status) {
    const labels = {
        todo: '待办',
        in_progress: '进行中',
        waiting: '等待',
        blocked: '阻塞',
        paused: '暂缓',
        done: '完成',
        cancelled: '取消'
    };
    return labels[status] || status;
}

function formatPriority(priority) {
    if (priority >= 3) {
        return '高优先级';
    }
    if (priority === 2) {
        return '中优先级';
    }
    return '低优先级';
}

async function loadFiles(category, gridId) {
    const grid = document.getElementById(gridId);

    try {
        const response = await fetch(`${API_BASE}/api/${category}`);
        const files = await response.json();

        if (files.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">EMPTY</div>
                    <div class="empty-state-text">暂无内容</div>
                </div>
            `;
            return;
        }

        grid.innerHTML = files.map(file => `
            <div class="file-card" data-path="${escapeHtml(file.path)}">
                <div class="file-card-title">${escapeHtml(file.title)}</div>
                <div class="file-card-meta">
                    ${formatDate(file.modified)}
                    ${file.editable ? '<span class="inline-badge">可编辑</span>' : ''}
                </div>
            </div>
        `).join('');

        grid.querySelectorAll('.file-card').forEach(card => {
            card.addEventListener('click', () => openFile(card.dataset.path));
        });
    } catch (error) {
        console.error(`加载 ${category} 失败:`, error);
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">ERR</div>
                <div class="empty-state-text">加载失败，请检查服务器</div>
            </div>
        `;
    }
}

// ===== 快速录入 =====
function initCaptureForm() {
    document.querySelectorAll('#capture-kind-tabs .segment').forEach(button => {
        button.addEventListener('click', () => setCaptureKind(button.dataset.kind));
    });

    ['capture-title', 'capture-body', 'capture-project', 'capture-tags', 'capture-priority', 'capture-due-date'].forEach(id => {
        const field = document.getElementById(id);
        if (!field) {
            return;
        }
        field.addEventListener('input', saveCaptureDraft);
        field.addEventListener('change', saveCaptureDraft);
    });

    document.getElementById('capture-submit').addEventListener('click', submitCapture);
    document.getElementById('capture-clear').addEventListener('click', clearCaptureDraft);
    activateCaptureKind(currentCaptureKind);
    restoreCaptureDraft();
}

function startCapture(kind) {
    showSection('dashboard');
    setCaptureKind(kind);
    document.getElementById('capture-title').focus();
}

function setCaptureKind(kind) {
    if (!KIND_LABELS[kind] || kind === 'file_edit_review') {
        return;
    }
    if (!editingInboxId) {
        saveCaptureDraft();
    }
    editingInboxId = null;
    updateCaptureSubmitLabel();
    activateCaptureKind(kind);
    restoreCaptureDraft();
}

function activateCaptureKind(kind) {
    currentCaptureKind = kind;
    document.querySelectorAll('#capture-kind-tabs .segment').forEach(button => {
        button.classList.toggle('active', button.dataset.kind === kind);
    });
    document.getElementById('capture-body').placeholder = BODY_PLACEHOLDERS[kind] || BODY_PLACEHOLDERS.freeform;
}

function readCaptureFields() {
    return {
        kind: currentCaptureKind,
        title: document.getElementById('capture-title').value.trim(),
        body: document.getElementById('capture-body').value.trim(),
        context: {
            project: document.getElementById('capture-project').value.trim(),
            tags: splitTags(document.getElementById('capture-tags').value),
            priority: document.getElementById('capture-priority').value,
            due_date: document.getElementById('capture-due-date').value,
            target_path: ''
        }
    };
}

function writeCaptureFields(item) {
    document.getElementById('capture-title').value = item.title || '';
    document.getElementById('capture-body').value = item.body || '';
    document.getElementById('capture-project').value = item.context?.project || '';
    document.getElementById('capture-tags').value = (item.context?.tags || []).join(', ');
    document.getElementById('capture-priority').value = item.context?.priority || '';
    document.getElementById('capture-due-date').value = item.context?.due_date || '';
}

function getDraftKey() {
    return `dashboard.captureDraft.v1.${currentCaptureKind}`;
}

function saveCaptureDraft() {
    if (editingInboxId) {
        return;
    }
    const draft = readCaptureFields();
    localStorage.setItem(getDraftKey(), JSON.stringify(draft));
    setCaptureStatus('草稿已保存');
}

function restoreCaptureDraft() {
    const rawDraft = localStorage.getItem(getDraftKey());
    if (!rawDraft) {
        writeCaptureFields({ context: {} });
        setCaptureStatus('草稿自动保存');
        return;
    }

    try {
        const draft = JSON.parse(rawDraft);
        writeCaptureFields(draft);
        setCaptureStatus('已恢复本地草稿');
    } catch (error) {
        console.warn('恢复草稿失败:', error);
        writeCaptureFields({ context: {} });
    }
}

function clearCaptureDraft() {
    localStorage.removeItem(getDraftKey());
    editingInboxId = null;
    writeCaptureFields({ context: {} });
    updateCaptureSubmitLabel();
    setCaptureStatus('草稿已清空');
}

async function submitCapture() {
    const payload = readCaptureFields();
    if (!payload.title && !payload.body) {
        setCaptureStatus('请至少填写标题或正文', 'warning');
        return;
    }

    const isEditing = Boolean(editingInboxId);
    const url = isEditing
        ? `${API_BASE}/api/inbox/${encodeURIComponent(editingInboxId)}`
        : `${API_BASE}/api/inbox`;
    const method = isEditing ? 'PATCH' : 'POST';

    setCaptureStatus(isEditing ? '正在更新缓存项...' : '正在写入缓存区...');

    try {
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '保存失败');
        }

        if (!isEditing) {
            localStorage.removeItem(getDraftKey());
        }
        editingInboxId = null;
        writeCaptureFields({ context: {} });
        updateCaptureSubmitLabel();
        setCaptureStatus(isEditing ? '缓存项已更新' : '已存入缓存区，Agent 下次会接管', 'success');
        await loadDashboard();
    } catch (error) {
        console.error('提交缓存失败:', error);
        setCaptureStatus(`保存失败：${error.message}`, 'warning');
    }
}

function setCaptureStatus(message, tone = '') {
    const status = document.getElementById('capture-status');
    status.textContent = message;
    status.className = `status-pill ${tone ? `is-${tone}` : ''}`.trim();
}

function updateCaptureSubmitLabel() {
    document.getElementById('capture-submit').textContent = editingInboxId ? '更新缓存项' : '存入缓存区';
}

// ===== Inbox =====
async function loadInbox() {
    try {
        const response = await fetch(`${API_BASE}/api/inbox?status=all`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '加载缓存区失败');
        }

        inboxItemsById = new Map(data.items.map(item => [item.id, item]));
        updateInboxCounts(data.counts || {});

        const dashboardItems = data.items
            .filter(item => item.status !== 'processed')
            .slice(0, 6);
        renderInboxList('dashboard-inbox-list', dashboardItems, true);
        renderInboxList('inbox-list', data.items, false);
    } catch (error) {
        console.error('加载缓存区失败:', error);
        renderInboxError('dashboard-inbox-list', error.message);
        renderInboxError('inbox-list', error.message);
    }
}

function updateInboxCounts(counts) {
    setText('inbox-count', counts.pending || 0);
    setText('inbox-pending-count', counts.pending || 0);
    setText('inbox-failed-count', counts.failed || 0);
    setText('inbox-cancelled-count', counts.cancelled || 0);
    setText('inbox-page-pending-count', counts.pending || 0);
    setText('inbox-page-failed-count', counts.failed || 0);
    setText('inbox-page-cancelled-count', counts.cancelled || 0);
    setText('inbox-page-processed-count', counts.processed || 0);
}

function renderInboxList(containerId, items, compact) {
    const container = document.getElementById(containerId);
    if (!container) {
        return;
    }

    if (!items.length) {
        container.innerHTML = `
            <div class="empty-state small">
                <div class="empty-state-icon">EMPTY</div>
                <div class="empty-state-text">缓存区是空的</div>
            </div>
        `;
        return;
    }

    container.innerHTML = items.map(item => `
        <article class="inbox-item status-${escapeHtml(item.status || 'pending')}">
            <div class="inbox-item-top">
                <span class="status-badge">${escapeHtml(STATUS_LABELS[item.status] || item.status || '待处理')}</span>
                <span class="kind-badge">${escapeHtml(KIND_LABELS[item.kind] || item.kind || '输入')}</span>
                <span class="inbox-time">${formatInboxTime(item.updated_at || item.created_at)}</span>
            </div>
            <h3>${escapeHtml(item.title || '(无标题)')}</h3>
            <p>${escapeHtml(compact ? truncateText(item.body || '', 120) : item.body || '')}</p>
            ${compact ? '' : `
                <div class="inbox-context">
                    ${item.context?.project ? `<span>项目：${escapeHtml(item.context.project)}</span>` : ''}
                    ${item.context?.priority ? `<span>优先级：${escapeHtml(item.context.priority)}</span>` : ''}
                    ${item.context?.due_date ? `<span>截止：${escapeHtml(item.context.due_date)}</span>` : ''}
                    ${(item.context?.tags || []).map(tag => `<span>#${escapeHtml(tag)}</span>`).join('')}
                </div>
            `}
            ${item.result?.summary ? `<p class="inbox-result">${escapeHtml(item.result.summary)}</p>` : ''}
            <div class="inbox-actions">
                ${item.status === 'pending' ? `
                    <button class="secondary-btn compact" data-inbox-action="edit" data-id="${escapeHtml(item.id)}">修改</button>
                    <button class="danger-btn compact" data-inbox-action="cancel" data-id="${escapeHtml(item.id)}">取消</button>
                ` : ''}
                ${compact ? '' : `<button class="danger-btn compact" data-inbox-action="delete" data-id="${escapeHtml(item.id)}">删除记录</button>`}
            </div>
        </article>
    `).join('');

    container.querySelectorAll('[data-inbox-action]').forEach(button => {
        button.addEventListener('click', event => {
            event.stopPropagation();
            const id = button.dataset.id;
            if (button.dataset.inboxAction === 'edit') {
                editInboxItem(id);
            } else if (button.dataset.inboxAction === 'cancel') {
                cancelInboxItem(id);
            } else if (button.dataset.inboxAction === 'delete') {
                deleteInboxItem(id);
            }
        });
    });
}

function renderInboxError(containerId, message) {
    const container = document.getElementById(containerId);
    if (!container) {
        return;
    }
    container.innerHTML = `
        <div class="empty-state small">
            <div class="empty-state-icon">ERR</div>
            <div class="empty-state-text">${escapeHtml(message)}</div>
        </div>
    `;
}

function editInboxItem(id) {
    const item = inboxItemsById.get(id);
    if (!item || item.status !== 'pending') {
        return;
    }
    editingInboxId = id;
    activateCaptureKind(item.kind);
    writeCaptureFields(item);
    updateCaptureSubmitLabel();
    setCaptureStatus('正在修改已有缓存项');
    showSection('dashboard');
    document.getElementById('capture-title').focus();
}

async function cancelInboxItem(id) {
    if (!confirm('确定取消这条缓存输入吗？内容会保留在已取消记录中。')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/inbox/${encodeURIComponent(id)}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '取消失败');
        }
        await loadDashboard();
    } catch (error) {
        console.error('取消缓存项失败:', error);
        alert(`取消失败：${error.message}`);
    }
}

async function deleteInboxItem(id) {
    const item = inboxItemsById.get(id);
    const status = item?.status || '';
    const message = status === 'pending'
        ? '确定彻底删除这条 pending 缓存记录吗？这通常只适合测试条目。'
        : '确定从缓存区历史中删除这条记录吗？正式归档内容不会被删除。';
    if (!confirm(message)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/inbox/${encodeURIComponent(id)}?hard=1`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '删除失败');
        }
        await loadDashboard();
        if (currentSection === 'inbox') {
            await loadInbox();
        }
    } catch (error) {
        console.error('删除缓存记录失败:', error);
        alert(`删除失败：${error.message}`);
    }
}

// ===== 文件查看器 / 编辑器 =====
function initFileModal() {
    document.getElementById('preview-mode-btn').addEventListener('click', () => setFileMode('preview'));
    document.getElementById('edit-mode-btn').addEventListener('click', () => setFileMode('edit'));
    document.getElementById('file-save-btn').addEventListener('click', saveCurrentFile);
}

async function openFile(path) {
    const modal = document.getElementById('file-modal');
    const title = document.getElementById('modal-title');
    const preview = document.getElementById('modal-preview');
    const editor = document.getElementById('modal-editor');

    currentFile = null;
    title.textContent = '加载中...';
    preview.innerHTML = '<p>正在加载文件内容...</p>';
    editor.value = '';
    setModalStatus('');
    modal.classList.add('active');
    setFileMode('preview');

    try {
        const response = await fetch(`${API_BASE}/api/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || '加载失败');
        }

        currentFile = data;
        title.textContent = data.name;
        preview.innerHTML = marked.parse(data.content);
        editor.value = data.content;
        document.getElementById('edit-mode-btn').disabled = !data.editable;
        document.getElementById('agent-review-toggle').checked = false;
        document.getElementById('agent-review-toggle').disabled = !data.editable;
        setModalStatus(data.editable ? '可编辑文件。保存前会自动备份。' : '此文件不可从 Dashboard 直接编辑。');
    } catch (error) {
        title.textContent = '错误';
        preview.innerHTML = `<p>加载失败: ${escapeHtml(error.message)}</p>`;
        document.getElementById('edit-mode-btn').disabled = true;
    }
}

function setFileMode(mode) {
    const preview = document.getElementById('modal-preview');
    const editor = document.getElementById('modal-editor');
    const saveButton = document.getElementById('file-save-btn');
    const previewButton = document.getElementById('preview-mode-btn');
    const editButton = document.getElementById('edit-mode-btn');

    if (mode === 'edit' && (!currentFile || !currentFile.editable)) {
        setModalStatus('此文件不可从 Dashboard 直接编辑。', 'warning');
        mode = 'preview';
    }

    preview.classList.toggle('hidden', mode !== 'preview');
    editor.classList.toggle('hidden', mode !== 'edit');
    saveButton.classList.toggle('hidden', mode !== 'edit');
    previewButton.classList.toggle('active', mode === 'preview');
    editButton.classList.toggle('active', mode === 'edit');

    if (mode === 'preview' && currentFile) {
        preview.innerHTML = marked.parse(editor.value || currentFile.content || '');
    }
}

async function saveCurrentFile() {
    if (!currentFile || !currentFile.editable) {
        setModalStatus('当前文件不可保存。', 'warning');
        return;
    }

    const editor = document.getElementById('modal-editor');
    const needsAgentReview = document.getElementById('agent-review-toggle').checked;
    setModalStatus('正在保存并创建备份...');

    try {
        const response = await fetch(`${API_BASE}/api/file/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: currentFile.path,
                content: editor.value,
                expected_mtime: currentFile.modified,
                needs_agent_review: needsAgentReview
            })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '保存失败');
        }

        currentFile.content = editor.value;
        currentFile.modified = data.modified;
        document.getElementById('modal-preview').innerHTML = marked.parse(currentFile.content);
        setFileMode('preview');
        setModalStatus(`已保存，备份位于 ${data.backup_path}`, 'success');
        if (needsAgentReview) {
            await loadDashboard();
        }
        if (currentSection === 'tasks') {
            loadTodos();
        } else if (currentSection !== 'dashboard' && currentSection !== 'inbox') {
            loadFiles(currentSection, `${currentSection}-grid`);
        }
    } catch (error) {
        console.error('保存文件失败:', error);
        setModalStatus(`保存失败：${error.message}`, 'warning');
    }
}

function closeModal() {
    document.getElementById('file-modal').classList.remove('active');
    currentFile = null;
}

document.getElementById('file-modal').addEventListener('click', (event) => {
    if (event.target.id === 'file-modal') {
        closeModal();
    }
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// ===== API Agent =====
function initAgentPanel() {
    const saveButton = document.getElementById('agent-save-profile');
    const clearButton = document.getElementById('agent-clear-profile');
    const testButton = document.getElementById('agent-test-profile');
    const previewButton = document.getElementById('agent-preview-run');
    const applyButton = document.getElementById('agent-apply-run');
    const activeSelect = document.getElementById('agent-active-profile');

    if (!saveButton) {
        return;
    }

    saveButton.addEventListener('click', saveAgentProfile);
    clearButton.addEventListener('click', clearAgentProfileForm);
    testButton.addEventListener('click', testAgentProfile);
    previewButton.addEventListener('click', () => runAgentProcess(false));
    applyButton.addEventListener('click', () => applyAgentPreview());
    activeSelect.addEventListener('change', () => activateAgentProfile(activeSelect.value));
}

async function loadAgentProfiles() {
    try {
        const response = await fetch(`${API_BASE}/api/agent/profiles`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '加载失败');
        }
        agentProfilesData = data;
        renderAgentProfiles();
        setAgentStatus('agent-profile-status', `${data.profiles.length} 个配置`);
    } catch (error) {
        setAgentStatus('agent-profile-status', `加载失败：${error.message}`, 'warning');
    }
}

function renderAgentProfiles() {
    const list = document.getElementById('agent-profile-list');
    const select = document.getElementById('agent-active-profile');
    if (!list || !select) {
        return;
    }

    const activeId = agentProfilesData.active_profile_id;
    const profiles = agentProfilesData.profiles || [];
    select.innerHTML = profiles.length
        ? profiles.map(profile => `
            <option value="${escapeHtml(profile.id)}" ${profile.id === activeId ? 'selected' : ''}>
                ${escapeHtml(profile.name)} · ${escapeHtml(profile.provider)} · ${escapeHtml(profile.model)}
            </option>
        `).join('')
        : '<option value="">暂无 API 配置</option>';

    list.innerHTML = profiles.length
        ? profiles.map(profile => `
            <div class="agent-profile-item ${profile.id === activeId ? 'active' : ''}">
                <div class="agent-profile-main">
                    <strong>${escapeHtml(profile.name)}</strong>
                    <span>${escapeHtml(profile.provider)} · ${escapeHtml(profile.model)} · ${escapeHtml(profile.base_url)}</span>
                </div>
                <button class="secondary-btn compact" data-agent-profile-edit="${escapeHtml(profile.id)}">编辑</button>
                <button class="danger-btn compact" data-agent-profile-delete="${escapeHtml(profile.id)}">删除</button>
            </div>
        `).join('')
        : '<div class="empty-state small"><div class="empty-state-text">还没有 API 配置</div></div>';

    list.querySelectorAll('[data-agent-profile-edit]').forEach(button => {
        button.addEventListener('click', () => fillAgentProfileForm(button.dataset.agentProfileEdit));
    });
    list.querySelectorAll('[data-agent-profile-delete]').forEach(button => {
        button.addEventListener('click', () => deleteAgentProfile(button.dataset.agentProfileDelete));
    });
}

function fillAgentProfileForm(profileId) {
    const profile = (agentProfilesData.profiles || []).find(item => item.id === profileId);
    if (!profile) {
        return;
    }
    document.getElementById('agent-profile-id').value = profile.id;
    document.getElementById('agent-profile-name').value = profile.name || '';
    document.getElementById('agent-provider').value = profile.provider || 'openai';
    document.getElementById('agent-base-url').value = profile.base_url || '';
    document.getElementById('agent-model').value = profile.model || '';
    document.getElementById('agent-api-key').value = '';
    setAgentStatus('agent-profile-status', `正在编辑：${profile.name}`);
}

function clearAgentProfileForm() {
    ['agent-profile-id', 'agent-profile-name', 'agent-base-url', 'agent-model', 'agent-api-key'].forEach(id => {
        document.getElementById(id).value = '';
    });
    document.getElementById('agent-provider').value = 'openai';
    setAgentStatus('agent-profile-status', '表单已清空');
}

async function saveAgentProfile() {
    const payload = {
        id: document.getElementById('agent-profile-id').value.trim(),
        name: document.getElementById('agent-profile-name').value.trim(),
        provider: document.getElementById('agent-provider').value,
        base_url: document.getElementById('agent-base-url').value.trim(),
        model: document.getElementById('agent-model').value.trim(),
        api_key: document.getElementById('agent-api-key').value.trim()
    };

    try {
        setAgentStatus('agent-profile-status', '保存中...');
        const response = await fetch(`${API_BASE}/api/agent/profiles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '保存失败');
        }
        agentProfilesData = data;
        renderAgentProfiles();
        clearAgentProfileForm();
        setAgentStatus('agent-profile-status', '已保存', 'success');
    } catch (error) {
        setAgentStatus('agent-profile-status', `保存失败：${error.message}`, 'warning');
    }
}

async function activateAgentProfile(profileId) {
    if (!profileId) {
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/api/agent/profiles/${encodeURIComponent(profileId)}/active`, {
            method: 'PATCH'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '切换失败');
        }
        agentProfilesData = data;
        renderAgentProfiles();
        setAgentStatus('agent-profile-status', '已切换', 'success');
    } catch (error) {
        setAgentStatus('agent-profile-status', `切换失败：${error.message}`, 'warning');
    }
}

async function deleteAgentProfile(profileId) {
    try {
        const response = await fetch(`${API_BASE}/api/agent/profiles/${encodeURIComponent(profileId)}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '删除失败');
        }
        agentProfilesData = data;
        renderAgentProfiles();
        clearAgentProfileForm();
        setAgentStatus('agent-profile-status', '已删除', 'success');
    } catch (error) {
        setAgentStatus('agent-profile-status', `删除失败：${error.message}`, 'warning');
    }
}

async function testAgentProfile() {
    const profileId = document.getElementById('agent-active-profile').value;
    const output = document.getElementById('agent-run-output');
    if (!profileId) {
        setAgentStatus('agent-run-status', '请先保存 API 配置', 'warning');
        return;
    }

    try {
        setAgentStatus('agent-run-status', '测试连接中...');
        output.textContent = '正在发送最小测试请求...';
        const response = await fetch(`${API_BASE}/api/agent/profiles/${encodeURIComponent(profileId)}/test`, {
            method: 'POST'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '测试失败');
        }
        output.textContent = `连接成功：${data.response_preview || ''}`;
        setAgentStatus('agent-run-status', '连接成功', 'success');
    } catch (error) {
        output.textContent = `测试失败：${error.message}`;
        setAgentStatus('agent-run-status', '连接失败', 'warning');
    }
}

async function runAgentProcess(applyNow) {
    const profileId = document.getElementById('agent-active-profile').value;
    const output = document.getElementById('agent-run-output');
    const applyButton = document.getElementById('agent-apply-run');
    if (!profileId) {
        setAgentStatus('agent-run-status', '请先保存 API 配置', 'warning');
        return;
    }

    try {
        setAgentStatus('agent-run-status', applyNow ? '处理中...' : '生成预览中...');
        output.textContent = '正在调用 API 处理缓存区，请稍等...';
        applyButton.disabled = true;
        const response = await fetch(`${API_BASE}/api/agent/process-inbox`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_id: profileId, apply: applyNow })
        });
        const data = await response.json();
        if (!response.ok) {
            const runSuffix = data.run_id ? `（run: ${data.run_id}）` : '';
            throw new Error(`${data.error || '处理失败'}${runSuffix}`);
        }
        lastAgentRunId = data.run_id || '';
        output.textContent = JSON.stringify(data.plan, null, 2);
        applyButton.disabled = applyNow || !lastAgentRunId;
        setAgentStatus('agent-run-status', applyNow ? '已应用' : '预览已生成', 'success');
        await loadInbox();
        await loadDashboard();
    } catch (error) {
        output.textContent = `处理失败：${error.message}`;
        setAgentStatus('agent-run-status', '处理失败', 'warning');
    }
}

async function applyAgentPreview() {
    if (!lastAgentRunId) {
        setAgentStatus('agent-run-status', '没有可应用的预览', 'warning');
        return;
    }

    const output = document.getElementById('agent-run-output');
    try {
        setAgentStatus('agent-run-status', '应用中...');
        const response = await fetch(`${API_BASE}/api/agent/process-inbox`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ run_id: lastAgentRunId, apply: true })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '应用失败');
        }
        output.textContent = JSON.stringify({
            summary: data.plan?.summary || '',
            applied_actions: data.applied_actions || [],
            warnings: data.plan?.warnings || []
        }, null, 2);
        document.getElementById('agent-apply-run').disabled = true;
        setAgentStatus('agent-run-status', '已应用', 'success');
        await loadInbox();
        await loadDashboard();
        if (currentSection === 'tasks') {
            await loadTodos();
        }
    } catch (error) {
        output.textContent = `应用失败：${error.message}`;
        setAgentStatus('agent-run-status', '应用失败', 'warning');
    }
}

function setAgentStatus(id, message, tone = '') {
    const element = document.getElementById(id);
    if (!element) {
        return;
    }
    element.textContent = message;
    element.className = `status-pill ${tone ? `is-${tone}` : ''}`.trim();
}

// ===== 软件更新 =====
function initAppPanel() {
    const checkButton = document.getElementById('app-check-update');
    const downloadButton = document.getElementById('app-download-update');
    const applyButton = document.getElementById('app-apply-update');
    if (!checkButton) {
        return;
    }
    checkButton.addEventListener('click', checkAppUpdate);
    downloadButton.addEventListener('click', downloadAppUpdate);
    applyButton.addEventListener('click', applyAppUpdate);
    loadAppInfo();
}

async function loadAppInfo() {
    try {
        const response = await fetch(`${API_BASE}/api/app/info`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '加载失败');
        }
        setText('app-version', data.version || '-');
        setText('app-mode', `${data.packaged ? '打包版' : '源码模式'} · ${data.distribution || 'source'}`);
        setText('app-workspace', data.workspace_root || '-');
        setAppUpdateStatus(data.update_enabled ? '可检查更新' : '源码模式', data.update_enabled ? '' : 'warning');
        document.getElementById('app-download-update').disabled = true;
        document.getElementById('app-apply-update').disabled = true;
        document.getElementById('app-update-output').textContent = data.update_enabled
            ? '点击“检查更新”查看公共 release 中是否有新版程序。程序更新不会覆盖当前工作区。'
            : '当前是源码/私人工作区模式，软件内自动安装公共 release 已禁用。';
    } catch (error) {
        setAppUpdateStatus(`加载失败：${error.message}`, 'warning');
    }
}

async function checkAppUpdate() {
    const output = document.getElementById('app-update-output');
    try {
        setAppUpdateStatus('检查中...');
        output.textContent = '正在检查 GitHub Release...';
        const response = await fetch(`${API_BASE}/api/app/update/check`, { method: 'POST' });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '检查失败');
        }
        appUpdateState.latest_version = data.latest_version || '';
        document.getElementById('app-download-update').disabled = !data.update_available;
        document.getElementById('app-apply-update').disabled = true;
        output.textContent = JSON.stringify(data, null, 2);
        if (!data.enabled) {
            setAppUpdateStatus('源码模式', 'warning');
        } else if (data.update_available) {
            setAppUpdateStatus(`发现 ${data.latest_version}`, 'success');
        } else {
            setAppUpdateStatus('已是最新', 'success');
        }
    } catch (error) {
        output.textContent = `检查失败：${error.message}`;
        setAppUpdateStatus('检查失败', 'warning');
    }
}

async function downloadAppUpdate() {
    const output = document.getElementById('app-update-output');
    try {
        setAppUpdateStatus('下载中...');
        output.textContent = '正在下载并校验更新包...';
        const response = await fetch(`${API_BASE}/api/app/update/download`, { method: 'POST' });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '下载失败');
        }
        appUpdateState.downloaded_version = data.version || appUpdateState.latest_version;
        document.getElementById('app-apply-update').disabled = !appUpdateState.downloaded_version;
        output.textContent = JSON.stringify(data, null, 2);
        setAppUpdateStatus('已下载', 'success');
    } catch (error) {
        output.textContent = `下载失败：${error.message}`;
        setAppUpdateStatus('下载失败', 'warning');
    }
}

async function applyAppUpdate() {
    const output = document.getElementById('app-update-output');
    if (!appUpdateState.downloaded_version) {
        setAppUpdateStatus('没有可应用更新', 'warning');
        return;
    }
    try {
        setAppUpdateStatus('准备重启...');
        output.textContent = '正在启动外部更新器。Dashboard 会关闭并自动重启。';
        const response = await fetch(`${API_BASE}/api/app/update/apply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ version: appUpdateState.downloaded_version })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '应用失败');
        }
        output.textContent = JSON.stringify(data, null, 2);
        setAppUpdateStatus('正在重启', 'success');
    } catch (error) {
        output.textContent = `应用失败：${error.message}`;
        setAppUpdateStatus('应用失败', 'warning');
    }
}

function setAppUpdateStatus(message, tone = '') {
    const element = document.getElementById('app-update-status');
    if (!element) {
        return;
    }
    element.textContent = message;
    element.className = `status-pill ${tone ? `is-${tone}` : ''}`.trim();
}

// ===== 主题切换 =====
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    const icon = document.querySelector('.theme-icon');
    icon.textContent = newTheme === 'dark' ? 'LIGHT' : 'DARK';
}

(function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const icon = document.querySelector('.theme-icon');
    if (icon) {
        icon.textContent = savedTheme === 'dark' ? 'LIGHT' : 'DARK';
    }
})();

// ===== 工具函数 =====
function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function setModalStatus(message, tone = '') {
    const status = document.getElementById('modal-status');
    status.textContent = message;
    status.className = `modal-status ${tone ? `is-${tone}` : ''}`.trim();
}

function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatInboxTime(value) {
    if (!value) {
        return '';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function splitTags(value) {
    return value
        .replace(/，/g, ',')
        .split(',')
        .map(tag => tag.trim())
        .filter(Boolean);
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }
    return `${text.slice(0, maxLength)}...`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text ?? '';
    return div.innerHTML;
}
