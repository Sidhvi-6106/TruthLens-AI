document.getElementById('verifyBtn').addEventListener('click', async () => {
  document.getElementById('status').style.display = 'none';
  document.getElementById('result').style.display = 'block';
  
  const scoreDisplay = document.getElementById('scoreDisplay');
  const summaryText = document.getElementById('summaryText');
  
  scoreDisplay.textContent = 'Scanning...';
  summaryText.textContent = 'Extracting page content for TruthLens API...';
  
  // Get active tab content
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: () => document.body.innerText
  }, async (results) => {
    if (results && results[0] && results[0].result) {
      const pageText = results[0].result;
      
      try {
        const response = await fetch('https://truthlens-ai-hazel.vercel.app/api/verification/article', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: pageText.substring(0, 5000) }) // Send first 5k chars
        });
        
        const data = await response.json();
        const score = data.truthlens_score;
        
        scoreDisplay.textContent = `${score}%`;
        if (score >= 75) scoreDisplay.className = 'score high';
        else if (score >= 50) scoreDisplay.className = 'score medium';
        else scoreDisplay.className = 'score low';
        
        summaryText.textContent = `Verdict: ${data.label}. Political Bias: ${data.bias_analysis?.political_bias || 'Unknown'}.`;
      } catch (err) {
        scoreDisplay.textContent = 'Error';
        summaryText.textContent = 'Could not reach TruthLens API. Is the server running?';
      }
    }
  });
});

document.getElementById('resetBtn').addEventListener('click', () => {
  document.getElementById('status').style.display = 'block';
  document.getElementById('result').style.display = 'none';
});
