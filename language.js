/* Static language editions. All language links also work without JavaScript. */
window.siteT = text => (window.siteTranslations || {})[text] || text;
document.addEventListener('DOMContentLoaded', () => {
  const switches = document.querySelectorAll('.language-switcher');
  switches.forEach(drop => {
    drop.querySelector('button').addEventListener('click', () => {
      document.querySelectorAll('.dropdown').forEach(other => {
        if (other !== drop) {
          other.classList.remove('open');
          other.querySelector('button').setAttribute('aria-expanded', 'false');
        }
      });
    });
  });
  document.addEventListener('click', event => {
    switches.forEach(drop => {
      if (!drop.contains(event.target)) {
        drop.classList.remove('open');
        drop.querySelector('button').setAttribute('aria-expanded', 'false');
      }
    });
  });
});
