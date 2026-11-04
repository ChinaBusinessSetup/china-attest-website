(() => {
  const t = text => (window.siteTranslations || {})[text] || text;
  const form = document.querySelector('#contact-inquiry');
  if (!form) return;
  const message = form.elements.message;
  message.addEventListener('input', () => {
    document.querySelector('#contact-count').textContent = `${message.value.length} / 2000`;
  });
  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      const value = button.dataset.copy;
      const toast = document.querySelector('#toast');
      try {
        await navigator.clipboard.writeText(value);
        toast.textContent = `${t('Copied:')} ${value}`;
      } catch {
        toast.textContent = `${t('Email us at')} ${value}`;
      }
      toast.hidden = false;
      setTimeout(() => { toast.hidden = true; }, 6000);
    });
  });
  const button = form.querySelector('[type="submit"]');
  const result = document.querySelector('#contact-result');
  const idleLabel = button.innerHTML;
  let sending = false;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (sending || !form.reportValidity()) return;
    sending = true;
    button.disabled = true;
    button.textContent = t('Sending…');
    form.setAttribute('aria-busy', 'true');
    result.hidden = true;
    result.removeAttribute('data-error');
    const data = new FormData(form);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: data,
        headers: { Accept: 'application/json' },
        signal: controller.signal
      });
      if (!response.ok) {
        const error = new Error('Submission failed');
        error.rateLimited = response.status === 429;
        throw error;
      }
      result.textContent = t('Thank you! Your enquiry has been submitted to China Attest. We will reply to the email address you provided.');
      // Keep any edits made while the request was in progress.
      const unchanged = ['name', 'email', 'service', 'message'].every(name =>
        form.elements[name].value === data.get(name)
      );
      if (unchanged) {
        form.reset();
        document.querySelector('#contact-count').textContent = '0 / 2000';
      }
    } catch (error) {
      result.dataset.error = 'true';
      result.textContent = error.rateLimited
        ? t('Too many submissions. Please wait a few minutes before trying again, or email chinaattest.team@gmail.com.')
        : t('We could not confirm your submission. Your details are still here. Please try again, or email chinaattest.team@gmail.com.');
    } finally {
      clearTimeout(timeout);
      sending = false;
      button.disabled = false;
      button.innerHTML = idleLabel;
      form.removeAttribute('aria-busy');
      result.hidden = false;
    }
  });
})();
