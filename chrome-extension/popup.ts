const API_BASE = 'http://localhost:8000';
const APP_NAME = 'RedditCommentAssistant';

let state = {
  token: null,
  user: null,
  personas: [],
  apiKey: null,
  services: {
    docker: false,
    mysql: false,
    redis: false,
    api: false
  }
};

document.addEventListener('DOMContentLoaded', async () => {
  await initializeApp();
});

async function initializeApp() {
  loadState();
  setupEventListeners();
  await checkServiceStatus();
  await loadSelectedText();
  loadApiKey();

  if (state.token) {
    showAppSection();
    await loadPersonas();
  } else {
    showLoginSection();
  }
}

function loadApiKey() {
  chrome.storage.local.get(['apiKey'], (result) => {
    if (result.apiKey) {
      state.apiKey = result.apiKey;
      document.getElementById('api-key').value = result.apiKey;
    }
  });
}

function saveApiKey(key) {
  state.apiKey = key;
  chrome.storage.local.set({ apiKey: key });
}

async function loadSelectedText() {
  chrome.storage.local.get(['selectedText'], (result) => {
    if (result.selectedText) {
      document.getElementById('post-content').value = result.selectedText;
      chrome.storage.local.remove(['selectedText']);
    }
  });
}

function loadState() {
  chrome.storage.local.get(['token', 'user'], (result) => {
    if (result.token) {
      state.token = result.token;
      state.user = result.user;
    }
  });
}

function saveState() {
  chrome.storage.local.set({ token: state.token, user: state.user });
}

async function checkServiceStatus() {
  updateServiceUI('docker', false);
  updateServiceUI('mysql', false);
  updateServiceUI('redis', false);

  try {
    const response = await fetch(`${API_BASE}/health`);
    if (response.ok) {
      state.services.api = true;
      state.services.mysql = true;
      state.services.redis = true;
      updateServiceUI('api', true);
      updateServiceUI('mysql', true);
      updateServiceUI('redis', true);
    }
  } catch {
    state.services.api = false;
    updateServiceUI('api', false);
  }

  document.getElementById('btn-start-all').textContent =
    state.services.api ? '✅ Running' : '▶ Start All';
}

function updateServiceUI(service, running) {
  const el = document.getElementById(`status-${service}`);
  if (el) {
    const dot = el.querySelector('.status-dot');
    dot.className = `status-dot ${running ? 'running' : 'stopped'}`;
  }
}

function showLoginSection() {
  document.getElementById('login-section').classList.remove('hidden');
  document.getElementById('app-section').classList.add('hidden');
}

function showAppSection() {
  document.getElementById('login-section').classList.add('hidden');
  document.getElementById('app-section').classList.remove('hidden');
  if (state.user) {
    document.getElementById('user-email').textContent = state.user.email;
  }
}

function setupEventListeners() {
  document.getElementById('btn-start-all').addEventListener('click', handleStartServices);
  document.getElementById('btn-login').addEventListener('click', handleEmailLogin);
  document.getElementById('btn-register').addEventListener('click', handleRegister);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);
  document.getElementById('btn-refresh-personas').addEventListener('click', loadPersonas);
  document.getElementById('btn-add-persona').addEventListener('click', showPersonaModal);
  document.getElementById('btn-cancel-persona').addEventListener('click', hidePersonaModal);
  document.getElementById('btn-save-persona').addEventListener('click', createPersona);
  document.getElementById('btn-generate').addEventListener('click', handleGenerateComments);
  document.getElementById('btn-save-api-key').addEventListener('click', handleSaveApiKey);
}

function handleSaveApiKey() {
  const apiKey = document.getElementById('api-key').value.trim();
  if (apiKey) {
    saveApiKey(apiKey);
    showMessage('API key saved!', 'success');
  } else {
    showMessage('Please enter a valid API key', 'error');
  }
}

async function handleStartServices() {
  const btn = document.getElementById('btn-start-all');

  if (state.services.api) {
    showMessage('All services are already running!', 'success');
    return;
  }

  btn.textContent = '⏳ Starting...';
  btn.disabled = true;

  try {
    const response = await fetch('http://localhost:8000/health');
    if (response.ok) {
      state.services.api = true;
      updateServiceUI('api', true);
      showMessage('API already running!', 'success');
    }
  } catch (e) {
    showMessage('API not responding. Please ensure backend is running', 'error', 8000);
  }

  btn.disabled = false;
  await checkServiceStatus();
}

async function handleEmailLogin() {
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const errorEl = document.getElementById('login-error');

  errorEl.classList.add('hidden');

  if (!email || !password) {
    errorEl.textContent = 'Please fill in all fields';
    errorEl.classList.remove('hidden');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (data.success === false) {
      throw new Error(data.message || 'Login failed');
    }

    state.token = data.data.token;
    state.user = data.data.user;
    saveState();
    showAppSection();
    await loadPersonas();
  } catch (error) {
    errorEl.textContent = error.message;
    errorEl.classList.remove('hidden');
  }
}

async function handleRegister() {
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const errorEl = document.getElementById('login-error');

  errorEl.classList.add('hidden');

  if (!email || !password) {
    errorEl.textContent = 'Please fill in all fields';
    errorEl.classList.remove('hidden');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: email.split('@')[0], email, password }),
    });

    const data = await response.json();

    if (data.success === false) {
      throw new Error(data.message || 'Registration failed');
    }

    errorEl.textContent = 'Registration successful! Please login.';
    errorEl.style.background = '#d4edda';
    errorEl.style.color = '#155724';
    errorEl.classList.remove('hidden');
  } catch (error) {
    errorEl.textContent = error.message;
    errorEl.style.background = '';
    errorEl.style.color = '';
    errorEl.classList.remove('hidden');
  }
}

function handleLogout() {
  state.token = null;
  state.user = null;
  chrome.storage.local.remove(['token', 'user']);
  showLoginSection();
  showMessage('Logged out successfully', 'success');
}

async function loadPersonas() {
  if (!state.token) return;

  try {
    const response = await fetch(`${API_BASE}/api/persona/list`, {
      headers: { Authorization: `Bearer ${state.token}` },
    });

    if (response.status === 401) {
      handleLogout();
      return;
    }

    const data = await response.json();
    state.personas = data.data || [];

    const select = document.getElementById('persona-select');
    select.innerHTML = '<option value="">No Persona (Default)</option>';
    state.personas.forEach(p => {
      const option = document.createElement('option');
      option.value = p.id;
      option.textContent = p.persona_name || 'Unnamed Persona';
      select.appendChild(option);
    });
  } catch (error) {
    showMessage('Failed to load personas', 'error');
  }
}

function showPersonaModal() {
  document.getElementById('persona-modal').classList.remove('hidden');
  document.getElementById('persona-name').value = '';
  document.getElementById('persona-description').value = '';
}

function hidePersonaModal() {
  document.getElementById('persona-modal').classList.add('hidden');
}

async function createPersona() {
  const name = document.getElementById('persona-name').value.trim();
  const description = document.getElementById('persona-description').value.trim();

  if (!name && !description) {
    showMessage('Please enter a name or description', 'error');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/persona/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify({
        persona_name: name || 'My Persona',
        persona_description: description
      }),
    });

    if (response.status === 401) {
      handleLogout();
      return;
    }

    const data = await response.json();

    if (data.success === false) {
      throw new Error(data.message || 'Failed to create persona');
    }

    hidePersonaModal();
    showMessage('Persona created!', 'success');
    await loadPersonas();
  } catch (error) {
    showMessage(error.message, 'error');
  }
}

async function handleGenerateComments() {
  const postContent = document.getElementById('post-content').value.trim();
  const permalink = document.getElementById('post-permalink').value.trim();
  const personaId = document.getElementById('persona-select').value;

  if (!postContent) {
    showMessage('Please enter post content', 'error');
    return;
  }

  const loadingEl = document.getElementById('loading');
  const commentsSection = document.getElementById('comments-section');
  const commentsList = document.getElementById('comments-list');

  loadingEl.classList.remove('hidden');
  commentsSection.classList.add('hidden');

  try {
    const response = await fetch(`${API_BASE}/api/comment/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify({
        post_content: postContent,
        permalink: permalink || null,
        persona_id: personaId ? parseInt(personaId) : null,
      }),
    });

    if (response.status === 401) {
      handleLogout();
      return;
    }

    if (response.status === 429) {
      throw new Error('Too many requests. Please wait a minute.');
    }

    const data = await response.json();

    if (data.success === false) {
      throw new Error(data.message || 'Generation failed');
    }

    renderComments(data.data.list || []);
    commentsSection.classList.remove('hidden');
    showMessage('Comments generated successfully!', 'success');
  } catch (error) {
    showMessage(error.message, 'error');
  } finally {
    loadingEl.classList.add('hidden');
  }
}

function renderComments(comments) {
  const commentsList = document.getElementById('comments-list');
  commentsList.innerHTML = '';

  comments.forEach(comment => {
    const card = document.createElement('div');
    card.className = 'comment-card';
    card.innerHTML = `
      <div class="comment-content">${escapeHtml(comment.content)}</div>
      <div class="comment-translation">🌐 ${escapeHtml(comment.translation || 'Translation unavailable')}</div>
      ${comment.suggestion ? `<div class="comment-suggestion">💡 ${escapeHtml(comment.suggestion)}</div>` : ''}
      <div class="comment-actions">
        <button class="btn btn-copy" data-comment-id="${comment.comment_id}">📋 Copy</button>
      </div>
    `;

    const copyBtn = card.querySelector('.btn-copy');
    copyBtn.addEventListener('click', () => handleCopyComment(comment, copyBtn));

    commentsList.appendChild(card);
  });
}

async function handleCopyComment(comment, button) {
  try {
    await navigator.clipboard.writeText(comment.content);

    button.textContent = '✅ Copied!';
    button.classList.add('copied');
    setTimeout(() => {
      button.textContent = '📋 Copy';
      button.classList.remove('copied');
    }, 2000);

    await fetch(`${API_BASE}/api/comment/use`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify({ comment_id: comment.comment_id }),
    });
  } catch (error) {
    showMessage('Failed to copy comment', 'error');
  }
}

function showMessage(text, type, duration = 3000) {
  const messageEl = document.getElementById('message');
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
  messageEl.classList.remove('hidden');
  setTimeout(() => {
    messageEl.classList.add('hidden');
  }, duration);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'postExtracted') {
    document.getElementById('post-content').value = message.content;
    document.getElementById('post-permalink').value = message.permalink || '';
  }
});

setInterval(checkServiceStatus, 5000);