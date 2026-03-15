const form = document.getElementById('audit-form');
const status = document.getElementById('status');

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  status.textContent = '';

  const website_url = document.getElementById('website_url').value.trim();
  const email = document.getElementById('email').value.trim();

  if (!website_url || !email) {
    status.textContent = 'Please enter both website and email.';
    return;
  }

  status.textContent = 'Running audit... This may take 10-20 seconds.';
  try {
    const res = await fetch('/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ website_url, email }),
    });
    const data = await res.json();
    if (!res.ok) {
      status.textContent = data.error || 'Audit failed. Please retry.';
      return;
    }

    localStorage.setItem('auditReport', JSON.stringify(data.report));
    window.location.href = '/result';
  } catch (err) {
    status.textContent = 'Server error. Please try again.';
    console.error(err);
  }
});
