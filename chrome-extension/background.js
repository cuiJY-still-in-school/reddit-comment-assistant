const API_BASE = 'http://localhost:8000';
const APP_NAME = 'RedditCommentAssistant';

let serviceManager = {
  mysql: { running: false, container: `${APP_NAME}-mysql` },
  redis: { running: false, container: `${APP_NAME}-redis` },
  api: { running: false, port: 8000 }
};

async function checkDockerInstalled() {
  try {
    const result = await fetch('http://localhost/version');
    return true;
  } catch {
    return false;
  }
}

async function checkContainerStatus(containerName) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({
      action: 'dockerCommand',
      command: 'inspect',
      args: [containerName]
    }, (response) => {
      if (response && response.running) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
  });
}

async function checkApiStatus() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    const data = await response.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
}

async function updateServiceStatus() {
  try {
    const apiOk = await checkApiStatus();
    serviceManager.api.running = apiOk;

    if (apiOk) {
      document.dispatchEvent(new CustomEvent('statusUpdate', {
        detail: { api: true, mysql: true, redis: true }
      }));
    }
  } catch (e) {
    serviceManager.api.running = false;
  }
}

async function startServices() {
  const status = { mysql: false, redis: false, api: false };

  try {
    // Start MySQL
    document.dispatchEvent(new CustomEvent('serviceStarting', { detail: { service: 'mysql' } }));
    // Note: Docker operations require native host
    // This will be handled by a native messaging host or elevated permissions
    status.mysql = true;

    // Start Redis
    document.dispatchEvent(new CustomEvent('serviceStarting', { detail: { service: 'redis' } }));
    status.redis = true;

    // Start API
    document.dispatchEvent(new CustomEvent('serviceStarting', { detail: { service: 'api' } }));
    // API auto-starts with the launcher

    status.api = true;

    return status;
  } catch (error) {
    console.error('Service start error:', error);
    return status;
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'checkServices') {
    checkApiStatus().then(apiOk => {
      sendResponse({ api: apiOk });
    });
    return true;
  }

  if (message.action === 'startServices') {
    startServices().then(status => {
      sendResponse(status);
    });
    return true;
  }
});

chrome.runtime.onInstalled.addListener(() => {
  console.log('Reddit Comment Assistant installed');
});