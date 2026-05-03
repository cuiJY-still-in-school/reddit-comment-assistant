const SELECTORS = {
  postContent: [
    '[data-testid="post-container"] [data-testid="post-content"]',
    '.Post .md-container',
    '.s-desktop-shadow-content p',
    '[data-click-id="body"] p',
    '.usertext-body p',
  ],
  postTitle: [
    '[data-testid="post-container"] h1',
    '.Post .title',
    '[data-click-id="title"]',
    '.titlebox h1',
  ],
  permalink: [
    '[data-testid="post-container"] a[data-click-id="timestamp"]',
    '.Post .timestamp',
    '[data-click-id="timestamp"]',
  ],
};

function extractPostContent() {
  let content = '';
  let title = '';
  let permalink = '';

  for (const selector of SELECTORS.postContent) {
    const el = document.querySelector(selector);
    if (el) {
      content = el.innerText.trim();
      if (content.length > 10) break;
    }
  }

  for (const selector of SELECTORS.postTitle) {
    const el = document.querySelector(selector);
    if (el) {
      title = el.innerText.trim();
      if (title) break;
    }
  }

  const timestampEl = document.querySelector('a[data-click-id="timestamp"]');
  if (timestampEl) {
    const postLink = timestampEl.closest('a');
    if (postLink && postLink.href) {
      permalink = postLink.href.split('?')[0];
    }
  }

  if (!permalink && window.location.pathname.includes('/comments/')) {
    permalink = window.location.origin + window.location.pathname;
  }

  if (content.length > 10) {
    return {
      content: title ? `${title}\n\n${content}` : content,
      permalink,
      success: true,
    };
  }

  return { success: false };
}

function createFloatingButton() {
  const button = document.createElement('button');
  button.id = 'reddit-assistant-extract-btn';
  button.innerHTML = '📤 Extract Post';
  button.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 999999;
    padding: 12px 20px;
    background: #ff4500;
    color: white;
    border: none;
    border-radius: 25px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(255, 69, 0, 0.4);
    transition: all 0.2s;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  `;

  button.addEventListener('mouseenter', () => {
    button.style.transform = 'scale(1.05)';
    button.style.boxShadow = '0 6px 16px rgba(255, 69, 0, 0.5)';
  });

  button.addEventListener('mouseleave', () => {
    button.style.transform = 'scale(1)';
    button.style.boxShadow = '0 4px 12px rgba(255, 69, 0, 0.4)';
  });

  button.addEventListener('click', () => {
    const result = extractPostContent();
    if (result.success) {
      chrome.runtime.sendMessage({
        action: 'postExtracted',
        content: result.content,
        permalink: result.permalink,
      });
      button.textContent = '✓ Extracted!';
      button.style.background = '#28a745';
      setTimeout(() => {
        button.textContent = '📤 Extract Post';
        button.style.background = '#ff4500';
      }, 2000);
    } else {
      button.textContent = '✗ No post found';
      setTimeout(() => {
        button.textContent = '📤 Extract Post';
      }, 2000);
    }
  });

  document.body.appendChild(button);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', createFloatingButton);
} else {
  createFloatingButton();
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPostData') {
    const postData = extractPostData();
    sendResponse({ success: true, data: postData });
  }
  if (request.action === 'textSelected') {
    chrome.storage.local.set({ selectedText: request.text }, () => {
      sendResponse({ success: true });
    });
    return true;
  }
  return true;
});
