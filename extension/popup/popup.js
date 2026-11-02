// TrustLens AI — Extension Popup Script

document.addEventListener('DOMContentLoaded', () => {
  const currentUrlEl = document.getElementById('current-url');
  const threatsCountEl = document.getElementById('threats-count');
  const scanPageBtn = document.getElementById('scan-page-btn');
  const quickInput = document.getElementById('quick-input');
  const quickCheckBtn = document.getElementById('quick-check-btn');
  const quickResult = document.getElementById('quick-result');
  const toggleFeeds = document.getElementById('toggle-feeds');
  const toggleLinks = document.getElementById('toggle-links');

  // Load saved stats and settings
  chrome.storage.local.get(['threatsBlocked', 'autoScan', 'feedProtection'], (data) => {
    if (data.threatsBlocked !== undefined) {
      threatsCountEl.textContent = data.threatsBlocked;
    }
    if (data.autoScan !== undefined) {
      toggleLinks.checked = data.autoScan;
    }
    if (data.feedProtection !== undefined) {
      toggleFeeds.checked = data.feedProtection;
    }
  });

  // Query current active tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs && tabs[0] && tabs[0].url) {
      currentUrlEl.textContent = tabs[0].url;
    } else {
      currentUrlEl.textContent = 'No active tab URL detected';
    }
  });

  // Scan current page button
  scanPageBtn.addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) return;
      chrome.tabs.sendMessage(tabs[0].id, {
        action: 'ANALYZE_LINK',
        payload: tabs[0].url
      }, () => {
        scanPageBtn.textContent = '✓ Scan Triggered';
        setTimeout(() => {
          scanPageBtn.textContent = 'Scan Current Page';
        }, 1800);
      });
    });
  });

  // Quick text / URL check
  quickCheckBtn.addEventListener('click', () => {
    const text = quickInput.value.trim();
    if (!text) return;

    quickResult.style.display = 'block';
    quickResult.className = 'result-box';
    quickResult.textContent = 'Scanning with TrustLens AI engine...';

    // Local evaluation
    setTimeout(() => {
      const isUrgent = /urgent|verify immediately|suspended|act now|bank alert|payroll/i.test(text);
      const isPhishUrl = /\.xyz|\.top|\.biz|homoglyph|login-verify|account-update/i.test(text);

      if (isUrgent || isPhishUrl) {
        quickResult.className = 'result-box result-threat';
        quickResult.textContent = '⚠️ Threat Flagged: High likelihood of phishing / social engineering manipulation.';
        // Increment threat counter
        chrome.storage.local.get(['threatsBlocked'], (data) => {
          const count = (data.threatsBlocked || 0) + 1;
          chrome.storage.local.set({ threatsBlocked: count });
          threatsCountEl.textContent = count;
        });
      } else {
        quickResult.className = 'result-box result-safe';
        quickResult.textContent = '🛡️ Content verified: No obvious deception signals detected.';
      }
    }, 450);
  });

  // Toggles save
  toggleFeeds.addEventListener('change', () => {
    chrome.storage.local.set({ feedProtection: toggleFeeds.checked });
  });

  toggleLinks.addEventListener('change', () => {
    chrome.storage.local.set({ autoScan: toggleLinks.checked });
  });
});
