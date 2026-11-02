// TrustLens AI — Background Service Worker (Manifest V3)

chrome.runtime.onInstalled.addListener(() => {
  // Create Context Menus
  chrome.contextMenus.create({
    id: "trustlens-scan-selection",
    title: "🛡️ Scan text with TrustLens AI",
    contexts: ["selection"]
  });

  chrome.contextMenus.create({
    id: "trustlens-scan-link",
    title: "🔍 Inspect link for phishing",
    contexts: ["link"]
  });

  chrome.contextMenus.create({
    id: "trustlens-scan-image",
    title: "🎭 Check image for deepfake",
    contexts: ["image"]
  });

  // Default settings
  chrome.storage.local.set({
    autoScan: true,
    feedProtection: true,
    threatsBlocked: 0,
    apiUrl: "http://localhost:8000"
  });

  console.log("TrustLens AI Extension Installed Successfully.");
});

// Context Menu Action Handler
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (!tab || !tab.id) return;

  if (info.menuItemId === "trustlens-scan-selection") {
    chrome.tabs.sendMessage(tab.id, {
      action: "ANALYZE_TEXT",
      payload: info.selectionText
    });
  } else if (info.menuItemId === "trustlens-scan-link") {
    chrome.tabs.sendMessage(tab.id, {
      action: "ANALYZE_LINK",
      payload: info.linkUrl
    });
  } else if (info.menuItemId === "trustlens-scan-image") {
    chrome.tabs.sendMessage(tab.id, {
      action: "ANALYZE_IMAGE",
      payload: info.srcUrl
    });
  }
});

// Listener for messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "INCREMENT_THREAT_COUNT") {
    chrome.storage.local.get(["threatsBlocked"], (data) => {
      const count = (data.threatsBlocked || 0) + 1;
      chrome.storage.local.set({ threatsBlocked: count });
      sendResponse({ success: true, count });
    });
    return true;
  }
});
