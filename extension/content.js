// TrustLens AI — Content Script (Real-time feed & link scanner)

const SUSPICIOUS_TLDS = ['.xyz', '.top', '.buzz', '.work', '.click', '.loan', '.fit', '.country', '.biz', '.cf', '.gq', '.tk', '.ml'];
const PHISH_KEYWORDS = ['secure-login', 'verify-account', 'update-billing', 'payroll-portal', 'wallet-connect', 'chase-security', 'paypal-verify', 'wellsfargo-auth'];
const HOMOGLYPH_REGEX = /[а-яА-Я\u0400-\u04FF]/; // Cyrillic homoglyphs spoofing Latin

function evaluateUrlRisk(urlStr) {
  try {
    const url = new URL(urlStr);
    const host = url.hostname.toLowerCase();

    // Check homoglyph attack
    if (HOMOGLYPH_REGEX.test(host)) {
      return { isThreat: true, reason: 'Homoglyph domain spoofing detected' };
    }

    // Check IP address used as domain
    if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(host)) {
      return { isThreat: true, reason: 'Direct IP URL used (common phishing pattern)' };
    }

    // Check suspicious TLDs
    for (const tld of SUSPICIOUS_TLDS) {
      if (host.endsWith(tld)) {
        return { isThreat: true, reason: `Suspicious high-risk TLD (${tld})` };
      }
    }

    // Check credential harvesting keywords
    for (const kw of PHISH_KEYWORDS) {
      if (urlStr.toLowerCase().includes(kw)) {
        return { isThreat: true, reason: `Credential harvesting pattern: "${kw}"` };
      }
    }
  } catch (e) {
    // Malformed URL
  }
  return { isThreat: false };
}

function scanLinksOnPage() {
  const links = document.querySelectorAll('a[href]:not([data-trustlens-scanned])');
  links.forEach(link => {
    link.setAttribute('data-trustlens-scanned', 'true');
    const href = link.href;
    if (!href || href.startsWith('javascript:') || href.startsWith('#')) return;

    const risk = evaluateUrlRisk(href);
    if (risk.isThreat) {
      link.classList.add('trustlens-flagged-link');
      
      const badge = document.createElement('span');
      badge.className = 'trustlens-warning-badge';
      badge.innerHTML = `⚠️ Phishing Risk: ${risk.reason}`;
      badge.title = 'Flagged by TrustLens AI Shield';
      
      link.parentNode?.insertBefore(badge, link.nextSibling);
      
      chrome.runtime.sendMessage({ action: 'INCREMENT_THREAT_COUNT' });
    }
  });
}

// In-Page Notification Modal for On-Demand Scans
function showInPageNotification(title, message, isWarning = false) {
  const existing = document.getElementById('trustlens-notification');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'trustlens-notification';
  toast.className = `trustlens-toast ${isWarning ? 'threat' : 'safe'}`;
  toast.innerHTML = `
    <div class="tl-toast-header">
      <span class="tl-toast-logo">🛡️ TrustLens AI</span>
      <button class="tl-toast-close">&times;</button>
    </div>
    <div class="tl-toast-title">${title}</div>
    <div class="tl-toast-body">${message}</div>
  `;

  document.body.appendChild(toast);

  toast.querySelector('.tl-toast-close').onclick = () => toast.remove();
  setTimeout(() => {
    if (toast.parentNode) toast.remove();
  }, 6000);
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.action === 'ANALYZE_LINK') {
    const risk = evaluateUrlRisk(req.payload);
    if (risk.isThreat) {
      showInPageNotification('Phishing Risk Detected', `${risk.reason} in link: ${req.payload}`, true);
    } else {
      showInPageNotification('Link Verified', `No obvious phishing signatures found: ${req.payload}`, false);
    }
  } else if (req.action === 'ANALYZE_TEXT') {
    const text = req.payload || '';
    const hasUrgency = /urgent|verify immediately|suspended|act now|bank alert/i.test(text);
    if (hasUrgency) {
      showInPageNotification('Potential Scam Text', 'Contains urgency cues & credential lures typical of phishing SMS/email.', true);
    } else {
      showInPageNotification('Text Analyzed', 'No active manipulation patterns detected.', false);
    }
  } else if (req.action === 'ANALYZE_IMAGE') {
    showInPageNotification('Image Sent to TrustLens', 'Analyzing noise residuals and PRNU consistency...', false);
  }
});

// Run initial link scan
scanLinksOnPage();

// MutationObserver for infinite scroll feeds (Twitter/X, Reddit, LinkedIn)
const observer = new MutationObserver(() => {
  scanLinksOnPage();
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});
