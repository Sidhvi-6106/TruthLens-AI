// TruthLens Content Script
// Automatically injects a trust score badge into articles (stub implementation)

function injectTruthBadge() {
  const h1 = document.querySelector('h1');
  if (h1 && !document.getElementById('truthlens-badge')) {
    const badge = document.createElement('div');
    badge.id = 'truthlens-badge';
    badge.style.display = 'inline-block';
    badge.style.marginLeft = '10px';
    badge.style.padding = '4px 8px';
    badge.style.background = '#0f766e';
    badge.style.color = 'white';
    badge.style.borderRadius = '4px';
    badge.style.fontSize = '12px';
    badge.style.fontWeight = 'bold';
    badge.style.verticalAlign = 'middle';
    badge.textContent = 'TruthLens Active';
    
    h1.appendChild(badge);
  }
}

// Run on page load
setTimeout(injectTruthBadge, 2000);
