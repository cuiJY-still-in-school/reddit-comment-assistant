{
  "manifest_version": 3,
  "name": "Reddit Comment Assistant",
  "version": "1.0.0",
  "description": "AI-powered Reddit comment assistant with style learning",
  "permissions": ["activeTab", "storage"],
  "host_permissions": ["https://*.reddit.com/*"],
  "action": {
    "default_popup": "popup/index.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "content_scripts": [
    {
      "matches": ["https://*.reddit.com/*"],
      "js": ["content/content.js"]
    }
  ],
  "background": {
    "service_worker": "background/background.js"
  }
}