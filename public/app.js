const backendInput = document.getElementById('backendUrl');
const checkBtn = document.getElementById('checkBtn');
const statusBox = document.getElementById('status');

async function checkBackend() {
  const baseUrl = backendInput.value.trim();
  if (!baseUrl) {
    statusBox.textContent = 'Please enter a backend URL.';
    return;
  }

  statusBox.textContent = 'Checking backend…';
  try {
    const response = await fetch(`${baseUrl}/health`);
    const data = await response.json();
    statusBox.textContent = `Backend connected: ${data.project || 'ok'}`;
  } catch (error) {
    statusBox.textContent = `Backend check failed: ${error.message}`;
  }
}

checkBtn.addEventListener('click', checkBackend);
